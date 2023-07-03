import logging
from functools import lru_cache

from humps import dekebabize
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
    volume: int | None = None
    issn: list[str] = Field(None, alias="ISSN")
    doi: str = Field(None, alias="DOI")
    url: str = Field(None, alias="URL")
    issue: str | None = None
    page: str | None = None
    language: str | None = None
    abstract: str | None = None
    update_policy: str | None = None
    funder: list[CrossrefFunder] | None = None
    published_print: CrossrefDate | None = None
    assertion: list[CrossrefAssertion] | None = None
    reference: list[CrossrefReference] | None = Field(default=None, repr=False)

    @property
    def short_title(self) -> str:
        if len(self.short_container_title) > 0:
            return self.short_container_title[0]
        else:
            return self.container_title[0]


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
    return CrossrefWork(**dekebabize(response.json()))
