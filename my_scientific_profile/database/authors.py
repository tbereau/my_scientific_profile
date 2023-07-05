from typing import Any
import pandas as pd
from dataclasses import asdict

from my_scientific_profile.authors.authors import Author
from my_scientific_profile.database.utils import (
    read_dataclass_records_from_s3,
    save_dataclass_records_to_s3,
)
from my_scientific_profile.papers.papers import fetch_all_paper_authors

__all__ = [
    "save_dataclass_records_to_s3",
    "load_all_paper_authors_from_s3",
    "convert_paper_authors_to_dataframe"
]


def save_all_paper_authors_to_s3(s3_client: Any, s3_bucket: str) -> None:
    authors = fetch_all_paper_authors()
    save_dataclass_records_to_s3(authors, s3_client, s3_bucket)


def load_all_paper_authors_from_s3(s3_client: Any, s3_bucket: str) -> list[Author]:
    return read_dataclass_records_from_s3(Author, s3_client, s3_bucket)


def convert_paper_authors_to_dataframe(authors: list[Author]) -> pd.DataFrame:
    return pd.json_normalize([asdict(author) for author in authors])
