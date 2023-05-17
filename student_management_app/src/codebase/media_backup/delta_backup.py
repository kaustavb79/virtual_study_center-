import os
import sys
from datetime import date
import pandas as pd
from backup_init import AwsS3Config, S3Utility, setup_custom_logger

today = date.today()

log = setup_custom_logger("delta_backup")


class DeltaMediaSync:

    def __init__(self, version, config, local_dir_path, s3_utils) -> None:
        self.local_dir_path = local_dir_path
        self.config = config
        self.folder_name = local_dir_path.replace("\\", "/").split("/")[-1]
        self.version = version
        self.bucket = self.config.getBucket()
        self.client = self.config.getS3ClientObject()
        self.s3_utils = s3_utils

    """
        Upload the media to the latest version 
    """

    def get_version_from_bucket(self):
        versions = self.config.getS3ClientObject().list_objects_v2(Bucket=self.config.getBucket(),
                                                                   Prefix=self.config.getPrefix(), Delimiter='/')
        # print(versions.get('CommonPrefixes'))
        versions = [v['Prefix'].split("/")[-2] for v in versions.get('CommonPrefixes') if "/v" in v['Prefix']]
        versions.sort(reverse=True)
        if versions:
            self.version = versions[0]

    """
        Delta backup of media folder...
            - s3://<bucket>/media_backups/<version>//delta_backups/{today}/media
            - s3://<bucket>/media_backups/<version>//delta_backups/{today}/logs
    """

    def upload_delta_changes_to_s3(self):

        self.get_version_from_bucket()
        delta_change_path = f"media_backups/{self.version}/delta_backups/"

        if os.path.exists(self.local_dir_path):
            if os.path.isdir(self.local_dir_path):
                if os.path.isdir("logs"):
                    for log_f in os.listdir("logs"):
                        if ".csv" in log_f:
                            date = log_f.split(".")[0]
                            upload_list = []
                            df_dict = pd.read_csv(f"logs/{log_f}").to_dict('records')
                            for dct in df_dict:
                                if "folder" in dct['event_type'] and dct['event_type'].split("_")[1] in ["created"]:
                                    upload_list.append(dct['change_log'].replace(os.sep, '/'))
                                elif "file" in dct['event_type'] and dct['event_type'].split("_")[1] in ["created",
                                                                                                         "modified"]:
                                    upload_list.append(dct['change_log'].replace(os.sep, '/'))

                            upload_list = set(upload_list)
                            # print(upload_list)
                            for x in upload_list:
                                if os.path.isfile(x):
                                    s3_file = os.path.join(delta_change_path, date, x).replace(os.sep, '/')
                                    local_file = x
                                    response = self.s3_utils.upload_file(source_file=local_file,
                                                                         destination_url=s3_file)
                                    log.info(f'Uploaded {local_file} to {s3_file}')

                            # upload delta log file
                            local_file = f"logs/{log_f}"
                            s3_file = os.path.join(delta_change_path, date, local_file).replace(os.sep, '/')
                            response = self.s3_utils.upload_file(source_file=local_file, destination_url=s3_file)
                            log.info(f'Uploaded delta change log {local_file} to {s3_file}')
                            os.remove(local_file)
            else:
                log.warning("%s is not a directory!!", self.local_dir_path)
        else:
            log.warning("%s doesn't exist!!", self.local_dir_path)


if __name__ == "__main__":
    argumentList = sys.argv[1:]
    """
        SERVER BUCKET: lueinsmartattendance-v1
        LOCAL TEST BUCKET: test-lms-v1
    """
    bucket = argumentList[0]
    config = AwsS3Config(bucket)
    s3_utils = S3Utility(config)

    local_dir_path = os.path.join(os.getcwd(), "media")
    if not os.path.isdir(local_dir_path):
        os.mkdir(local_dir_path)

    obj = DeltaMediaSync("v1", config, local_dir_path, s3_utils)
    obj.upload_delta_changes_to_s3()