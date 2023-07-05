import logging

from boto3 import client, resource
from decouple import config as environ

from my_scientific_profile.config.required_environment_variables import assert_all_environment_variables
from my_scientific_profile.config.config import get_s3_bucket

logger = logging.getLogger(__name__)

__all__ = ["S3_CLIENT", "S3_RESOURCE", "S3_BUCKET"]

assert_all_environment_variables("aws")

S3_BUCKET = get_s3_bucket()

S3_CLIENT = client(
    "s3",
    aws_access_key_id=environ("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=environ("AWS_SECRET_ACCESS_KEY"),
)

S3_RESOURCE = resource(
    "s3",
    aws_access_key_id=environ("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=environ("AWS_SECRET_ACCESS_KEY"),
)
