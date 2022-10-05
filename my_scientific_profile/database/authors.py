from my_scientific_profile.authors.authors import Author
from my_scientific_profile.database.utils import (
    read_dataclass_records_from_s3,
    save_dataclass_records_to_s3,
)
from my_scientific_profile.papers.papers import fetch_all_paper_authors

__all__ = ["save_dataclass_records_to_s3", "load_all_paper_authors_from_s3"]


def save_all_paper_authors_to_s3() -> None:
    authors = fetch_all_paper_authors()
    save_dataclass_records_to_s3(authors)


def load_all_paper_authors_from_s3() -> list[Author]:
    return read_dataclass_records_from_s3(Author)
