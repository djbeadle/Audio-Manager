import os

import boto3
from botocore.config import Config

from config import config

_current_env = os.getenv("FLASK_ENV")
_current_config = config[_current_env]

S3_CLIENT = boto3.client(
    's3',
    config=Config(signature_version='s3v4'),
    region_name=_current_config.AWS_REGION,
    aws_access_key_id=_current_config.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=_current_config.AWS_SECRET_ACCESS_KEY
)

def generate_presigned_post(filename, type, fields):
    """
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.generate_presigned_post

    Returns
    A dictionary with two elements: url and fields. Url is the url to post to.
    Fields is a dictionary filled with the form fields and respective values to use when submitting the post. For example:

    {
        'url': 'https://mybucket.s3.amazonaws.com
        'fields': {
            'acl': 'public-read',
            'key': 'mykey', 'signature': 'mysignature', 'policy': 'mybase64 encoded policy'
        }
    }
    """
    return S3_CLIENT.generate_presigned_post(
        _current_config.AWS_BUCKET_NAME,
        filename,
        fields,
        [{k:v} for k,v in fields.items()]
    )

def get_metadata(filename):
    return S3_CLIENT.head_object(
        Bucket=_current_config.AWS_BUCKET_NAME,
        Key=filename
    )
