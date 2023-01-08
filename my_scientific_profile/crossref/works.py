import logging
from functools import lru_cache

from humps import dekebabize
from pydantic import parse_obj_as
from pydantic.dataclasses import Field, dataclass
from requests import get

from my_scientific_profile.crossref.utils import (
    CrossrefAssertion,
    CrossrefAuthor,
    CrossrefContentDomain,
    CrossrefDate,
    CrossrefFunder,
    CrossrefLink,
    CrossrefReference,
    get_crossref_request_endpoint_template,
)

logger = logging.getLogger(__name__)


@dataclass(eq=True, frozen=True)
class CrossrefWorkMessage:
    indexed: CrossrefDate
    reference_count: int
    publisher: str
    content_domain: CrossrefContentDomain
    short_container_title: list[str]
    type: str
    created: CrossrefDate
    source: str
    is_referenced_by_count: int
    title: list[str]
    prefix: str
    author: list[CrossrefAuthor]
    member: int
    container_title: list[str]
    original_title: list[str]
    link: list[CrossrefLink]
    deposited: CrossrefDate
    score: int
    subtitle: list[str]
    short_title: list[str]
    issued: CrossrefDate
    volume: int = None
    issn: list[str] = Field(None, alias="ISSN")
    doi: str = Field(None, alias="DOI")
    url: str = Field(None, alias="URL")
    issue: str = None
    page: str = None
    language: str = None
    abstract: str = None
    update_policy: str = None
    funder: list[CrossrefFunder] = None
    published_print: CrossrefDate = None
    assertion: list[CrossrefAssertion] = None
    reference: list[CrossrefReference] = Field(default=None, repr=False)


@dataclass(eq=True, frozen=True)
class CrossrefWork:
    status: str
    message_type: str
    message_version: str
    message: CrossrefWorkMessage


@lru_cache()
def get_crossref_work_by_doi(doi: str) -> CrossrefWork:
    logger.info(f"fetching Crossref info for doi {doi}")
    endpoint = f"{get_crossref_request_endpoint_template()}/works/{doi}"
    response = get(endpoint)
    assert (
        response.status_code == 200
    ), f"unexpected status code {response.status_code}: {response.text}"
    return parse_obj_as(CrossrefWork, dekebabize(response.json()))
