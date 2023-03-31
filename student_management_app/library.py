import boto3
import os

from botocore.exceptions import ClientError
import requests
from django.conf import settings

import logging as log_print

def setup_custom_logger(name):
    formatter = log_print.Formatter(fmt='%(asctime)s - %(process)d - %(levelname)s - %(message)s')
    # fh = log_print.FileHandler(settings.LOGS_DIR + '/s3_utils.log')
    fh = log_print.FileHandler('E:\\PERSONAL\\KAUSTAV\\projects\\ut_prod\\study_center\\logs\s3_utils.log')
    fh.setFormatter(formatter)
    logger = log_print.getLogger(name)
    logger.setLevel(log_print.INFO)
    logger.addHandler(fh)
    return logger


log = setup_custom_logger("s3_utils")

def create_presigned_post(s3_client, bucket_name, object_name, fields=None, conditions=None, expiration=3600):
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
        response = s3_client.generate_presigned_post(bucket_name,
                                                     object_name,
                                                     Fields=fields,
                                                     Conditions=conditions,
                                                     ExpiresIn=expiration)
    except ClientError as e:
        log.error(e)
        return None

    return response


def upload_file(s3_client, source_file, destination_url, BUCKET_NAME):
    response = create_presigned_post(s3_client, BUCKET_NAME, destination_url)
    # print(response)
    if response is None:
        return None

    with open(source_file, 'rb') as f:
        files = {'file': (source_file, f)}
        http_response = requests.post(response['url'].replace('https', 'http'), data=response['fields'], files=files)
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


def upload_file_to_s3(bucket,local_file, s3_file):
    # Generate a presigned S3 POST URL

    s3_file_url, is_upload_successful = upload_file(s3_client=settings.S3_CLIENT, source_file=local_file, destination_url=s3_file,
                           BUCKET_NAME=bucket)
    log.info(f'Uploaded {local_file} to {s3_file}')
    return s3_file_url, is_upload_successful


