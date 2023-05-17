import subprocess
from datetime import date
import os
from backup_init import AwsS3Config, setup_custom_logger
import sys


log = setup_custom_logger("media_full_backup")


class MediaSync:

    def __init__(self, version, config, local_dir_path) -> None:
        self.DATESTAMP = date.today()
        self.local_dir_path = local_dir_path
        self.config = config
        self.folder_name = local_dir_path.replace("\\", "/").split("/")[-1]
        self.version = version
        self.bucket = self.config.getBucket()

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
        Full backup of media folder...
            - s3://<bucket>/media_backups/<version>/media
            - s3://<bucket>/media_backups/<version>/media_<date>
    """

    def sync_media_to_s3(self):

        self.get_version_from_bucket()
        s3_path_media = f"s3://{self.bucket}/media_backups/{self.version}/{self.folder_name}"
        s3_path_media_timestamp = f"s3://{self.bucket}/media_backups/{self.version}/{self.folder_name}_{self.DATESTAMP}"
        upload_paths = [s3_path_media, s3_path_media_timestamp]

        if os.path.exists(self.local_dir_path):
            if os.path.isdir(self.local_dir_path):
                for s3_path in upload_paths:
                    log.info("Uploading %s to %s bucket instance!", self.local_dir_path, s3_path)

                    # aws cli sync command
                    command = f"aws s3 sync {self.local_dir_path} {s3_path} --delete"
                    log.info("COMMAND: %s", command)

                    try:
                        subprocess.run(command.split(" "))
                    except Exception as e:
                        log.exception('Exception happened during media backup')
                        log.error("Uploading %s to %s bucket instance failed!", self.local_dir_path, s3_path)
                    else:
                        log.info("Uploaded %s to %s bucket instance!", self.local_dir_path, s3_path)
        else:
            log.warning("%s doesn't exist!!", self.local_dir_path)


if __name__ == "__main__":
    argumentList = sys.argv[1:]
    """
        SERVER BUCKET: lueinsmartattendance
        LOCAL TEST BUCKET: test-lms-v1
    """
    bucket = argumentList[0]
    config = AwsS3Config(bucket)
    local_dir_path = os.path.join(os.getcwd(), "media")

    if not os.path.isdir(local_dir_path):
        os.mkdir(local_dir_path)

    obj = MediaSync("v1", config, local_dir_path)
    obj.sync_media_to_s3()