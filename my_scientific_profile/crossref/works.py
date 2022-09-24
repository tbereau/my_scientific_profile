import logging
from dataclasses import dataclass, field
from typing import List, Optional

from dataclass_wizard import JSONSerializable
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
class CrossrefWork(JSONSerializable):
    status: str
    message_type: str
    message_version: str
    message: "CrossrefWorkMessage"


@dataclass(eq=True, frozen=True)
class CrossrefWorkMessage(JSONSerializable):
    indexed: CrossrefDate
    reference_count: int
    publisher: str
    content_domain: CrossrefContentDomain
    short_container_title: List[str]
    doi: str
    type: str
    created: CrossrefDate
    source: str
    is_referenced_by_count: int
    title: List[str]
    prefix: str
    volume: int
    author: List[CrossrefAuthor]
    member: int
    container_title: List[str]
    original_title: List[str]
    link: List[CrossrefLink]
    deposited: CrossrefDate
    score: int
    subtitle: List[str]
    short_title: List[str]
    issued: CrossrefDate
    url: str
    issn: List[str]
    issue: Optional[str] = field(default=None)
    page: Optional[str] = field(default=None)
    language: Optional[str] = field(default=None)
    abstract: Optional[str] = field(default=None)
    update_policy: Optional[str] = field(default=None)
    funder: Optional[List[CrossrefFunder]] = field(default=None)
    published_print: Optional[CrossrefDate] = field(default=None)
    assertion: Optional[List[CrossrefAssertion]] = field(default=None)
    reference: Optional[List[CrossrefReference]] = field(default=None, repr=False)


def get_crossref_work_by_doi(doi: str) -> CrossrefWork:
    logger.info(f"fetching Crossref info for doi {doi}")
    endpoint = f"{get_crossref_request_endpoint_template()}/works/{doi}"
    response = get(endpoint)
    assert (
        response.status_code == 200
    ), f"unexpected status code {response.status_code}: {response.text}"
    return CrossrefWork.from_dict(response.json())
