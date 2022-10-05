import logging

from boto3 import client, resource
from decouple import config as environ
from flask_s3 import FlaskS3

logger = logging.getLogger(__name__)

__all__ = ["s3", "s3_client", "s3_resource", "S3_BUCKET"]

S3_BUCKET = "my-scientific-profile"

s3 = FlaskS3()

s3_client = client(
    "s3",
    aws_access_key_id=environ("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=environ("AWS_SECRET_ACCESS_KEY"),
)
s3_resource = resource(
    "s3",
    aws_access_key_id=environ("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=environ("AWS_SECRET_ACCESS_KEY"),
)
