import logging
from typing import List, Optional

import humps
from pydantic.dataclasses import dataclass
from requests import get

import my_scientific_profile.utils  # noqa

logger = logging.getLogger(__name__)

__all__ = [
    "MY_SEMANTIC_ID",
    "SemanticScholarAuthor",
    "SemanticScholarPaper",
    "get_semantic_scholar_request_endpoint_template",
    "fetch_info_by_id",
]

MY_SEMANTIC_ID = 1969822


@dataclass(frozen=True)
class SemanticScholarAuthorDefault:
    author_id: int
    name: str


@dataclass(frozen=True)
class SemanticScholarPaperDefault:
    paper_id: str
    title: str


@dataclass(frozen=True)
class SemanticScholarAuthor:
    author_id: str
    name: str = None
    url: str = None
    citation_count: int = None
    h_index: int = None
    aliases: List[str] = None
    papers: List["SemanticScholarPaperDefault"] = None


@dataclass(frozen=True)
class SemanticScholarTldr:
    model: str
    text: str


@dataclass(frozen=True)
class SemanticScholarPaper:
    paper_id: str
    title: str = None
    authors: List[SemanticScholarAuthorDefault] = None
    abstract: str = None
    year: int = None
    venue: str = None
    is_open_access: bool = None
    tldr: SemanticScholarTldr = None


def get_semantic_scholar_request_endpoint_template() -> str:
    return "https://api.semanticscholar.org/graph/v1"


def fetch_info_by_id(
    info_id: str, info_type: str, fields: Optional[List[str]] = None
) -> dict:
    logger.info(f"fetching Semantic Scholar {info_type} info {info_id}")
    endpoint = (
        f"{get_semantic_scholar_request_endpoint_template()}/{info_type}/{info_id}"
    )
    if fields is not None:
        endpoint += "?fields=" + ",".join(fields)
    response = get(endpoint)
    if response.status_code != 200:
        return {}
    return humps.decamelize(response.json())
