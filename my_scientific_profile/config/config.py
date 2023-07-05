import logging
from yaml import YAMLObject

from my_scientific_profile import CONFIG

__all__ = [
    "get_my_orcid",
    "get_author_configs",
    "get_paper_configs",
    "get_abstract_from_config",
    "find_author_in_config",
    "get_authors_with_categories",
]

logger = logging.getLogger(__name__)


def get_my_orcid() -> str:
    return CONFIG["my-orcid"].get(str)


def get_s3_bucket() -> str:
    return CONFIG["s3-bucket"].get(str)


def get_author_configs() -> list[dict]:
    return [dict(e) for e in CONFIG["authors"].get()]


def get_paper_configs() -> list[dict]:
    return [dict(e) for e in CONFIG["papers"].get()]


def find_author_in_config(
    given: str, family: str, orcid: str = None
) -> YAMLObject | dict:
    author_configs = get_author_configs()
    for author in author_configs:
        if orcid is not None and author.get("orcid"):
            if author["orcid"] == orcid:
                return author
        else:
            if author["family"] == family and author["given"] == given:
                return author
    return {}


def get_abstract_from_config(doi: str) -> str:
    paper_configs = get_paper_configs()
    papers = [p for p in paper_configs if p["doi"] == doi]
    if len(papers) > 0:
        return papers[0]["abstract"]
    return ""


def get_authors_with_categories() -> list[dict]:
    authors = []
    for author in get_author_configs():
        if author.get("categories"):
            authors.append(author)
    return authors
