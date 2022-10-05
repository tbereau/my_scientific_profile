import logging
import os
from dataclasses import asdict
from gzip import GzipFile, decompress
from typing import Any

from bson.json_util import dumps as mongo_dumps
from bson.json_util import loads as mongo_loads

from my_scientific_profile.utils import ROOT_DIR

logger = logging.getLogger(__name__)


def save_dataclass_records_to_s3(
    records: list[Any], s3_client: Any, s3_bucket: str
) -> None:
    json_str = mongo_dumps([asdict(r) for r in records])
    json_bytes = json_str.encode("utf-8")
    file_name = f"records_{records[0].__class__.__name__.lower()}.gz"
    full_path = os.path.join(ROOT_DIR, file_name)
    with GzipFile(full_path, "w") as file_out:
        file_out.write(json_bytes)
    s3_client.upload_file(full_path, s3_bucket, f"database/{file_name}")
    os.remove(full_path)


def read_dataclass_records_from_s3(
    dataclass: type, s3_client: Any, s3_bucket: str
) -> list[Any]:
    key = f"database/records_{dataclass.__name__.lower()}.gz"
    raw_response = s3_client.get_object(Bucket=s3_bucket, Key=key)["Body"].read()
    response = mongo_loads(decompress(raw_response).decode("utf-8"))
    logger.info(f"response {response}")
    return [dataclass(**r) for r in response]
