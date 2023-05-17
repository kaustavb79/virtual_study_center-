import logging as log_print
import os
import boto3
import requests
from botocore.exceptions import ClientError

LOGS_DIR = "logs"

if os.path.exists(LOGS_DIR) and os.path.isdir(LOGS_DIR):
    print("LOGS_DIR: ", LOGS_DIR)
else:
    os.mkdir(LOGS_DIR)


def setup_custom_logger(name):
    formatter = log_print.Formatter(fmt='%(asctime)s - %(process)d - %(levelname)s - %(message)s')
    fh = log_print.FileHandler(LOGS_DIR + '/s3_media_backup.log')
    fh.setFormatter(formatter)
    logger = log_print.getLogger(name)
    logger.setLevel(log_print.INFO)
    logger.addHandler(fh)
    return logger


log = setup_custom_logger("s3_media_backup_utility")


class AwsS3Config:
    def __init__(self, Bucket) -> None:
        # Generate a presigned S3 POST URL
        session = boto3.Session(profile_name="luein_root")
        self.s3_client = session.client('s3')

        self.BUCKET_NAME = Bucket
        self.prefix = "media_backups/"

    def getS3ClientObject(self):
        return self.s3_client

    def getBucket(self):
        return self.BUCKET_NAME

    def getPrefix(self):
        return self.prefix


class S3Utility:

    def __init__(self, config) -> None:
        self.s3_client = config.getS3ClientObject()
        self.bucket_name = config.getBucket()

    def create_presigned_post(self, object_name, fields=None, conditions=None, expiration=3600):
        """Generate a presigned URL S3 POST request to upload a file

        :param bucket_name: string
        :param object_name: string
        :param fields: Dictionary of prefilled form fields
        :param conditions: List of conditions to include in the policy
        :param expiration: Time in seconds for the presigned URL to remain valid
        :return: Dictionary with the following keys:
            url: URL to post to
            fields: Dictionary of form fields and values to submit with the POST
        :return: None if error.
        """
        try:
            response = self.s3_client.generate_presigned_post(self.bucket_name,
                                                              object_name,
                                                              Fields=fields,
                                                              Conditions=conditions,
                                                              ExpiresIn=expiration)
        except ClientError as e:
            log.exception("Exception Occurred")
            return None

        return response

    def upload_file(self, source_file, destination_url):
        response = self.create_presigned_post(destination_url)
        # print(response)
        if response is None:
            return None

        with open(source_file, 'rb') as f:
            files = {'file': (source_file, f)}
            http_response = requests.post(response['url'].replace('https', 'http'), data=response['fields'],
                                          files=files)
        # If successful, returns HTTP status code 204
        s3_file_url = ""
        if http_response.status_code in [200, 201, 204]:
            log.info("File Uploaded successfully!!! Returned Status: %s", http_response.status_code)
            # print(response['url'] + response['fields']['key'])
            s3_file_url = response['url'] + response['fields']['key']
            is_upload_successful = True
        else:
            log.error("Upload Failed !!!! Status: %s", http_response.status_code)
            is_upload_successful = False

        return s3_file_url, is_upload_successful
