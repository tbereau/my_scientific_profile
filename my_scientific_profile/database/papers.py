from typing import Any

from my_scientific_profile.database.utils import (
    read_dataclass_records_from_s3,
    save_dataclass_records_to_s3,
)
from my_scientific_profile.papers.papers import Paper, fetch_all_paper_infos

__all__ = [
    "save_dataclass_records_to_s3",
    "load_all_papers_from_s3",
    "save_all_papers_to_s3",
]


def save_all_papers_to_s3(s3_client: Any, s3_bucket: str) -> None:
    papers = fetch_all_paper_infos()
    save_dataclass_records_to_s3(papers, s3_client, s3_bucket)


def load_all_papers_from_s3(s3_client: Any, s3_bucket: str) -> list[Paper]:
    return read_dataclass_records_from_s3(Paper, s3_client, s3_bucket)
