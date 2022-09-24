import logging
from dataclasses import dataclass, field
from typing import List, Optional

from dataclass_wizard import JSONSerializable
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
class SemanticScholarAuthorDefault(JSONSerializable):
    author_id: int
    name: str


@dataclass(frozen=True)
class SemanticScholarPaperDefault(JSONSerializable):
    paper_id: str
    title: str


@dataclass(frozen=True)
class SemanticScholarAuthor(JSONSerializable):
    author_id: str
    name: Optional[str] = field(default=None)
    url: Optional[str] = field(default=None)
    citation_count: Optional[int] = field(default=None)
    h_index: Optional[int] = field(default=None)
    aliases: Optional[List[str]] = field(default=None)
    papers: Optional[List["SemanticScholarPaperDefault"]] = field(default=None)


@dataclass(frozen=True)
class SemanticScholarPaper(JSONSerializable):
    paper_id: str
    title: Optional[str] = field(default=None)
    authors: Optional[List[SemanticScholarAuthorDefault]] = field(default=None)
    abstract: Optional[str] = field(default=None)
    year: Optional[int] = field(default=None)
    venue: Optional[str] = field(default=None)
    is_open_access: Optional[bool] = field(default=None)
    tldr: Optional["SemanticScholarTldr"] = field(default=None)


@dataclass(frozen=True)
class SemanticScholarTldr(JSONSerializable):
    model: str
    text: str


def get_semantic_scholar_request_endpoint_template() -> str:
    return f"https://api.semanticscholar.org/graph/v1"


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
    return response.json()
