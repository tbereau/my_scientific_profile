import logging
from functools import lru_cache

from humps import dekebabize
from pydantic.dataclasses import Field, dataclass

from my_scientific_profile.crossref.utils import (
    CrossrefAssertion,
    CrossrefAuthor,
    CrossrefContentDomain,
    CrossrefDate,
    CrossrefFunder,
    CrossrefInstitution,
    CrossrefLink,
    CrossrefReference,
    get_crossref_request_endpoint_template,
)
from my_scientific_profile.utils.http import fetch_json

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
    issued: CrossrefDate
    short_title: list[str] = Field(default_factory=list)
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
    subtype: str | None = None
    group_title: str | None = None
    institution: list[CrossrefInstitution] | None = None

    @property
    def venue_name(self) -> str | None:
        return _first(self.container_title)

    @property
    def venue_abbreviation(self) -> str | None:
        return _first(self.short_container_title)

    @property
    def institution_name(self) -> str | None:
        """The host Crossref names for posted content, whose container is empty."""
        if not self.institution:
            return None
        return _first([i.name for i in self.institution if i.name])


@dataclass(eq=True, frozen=True)
class CrossrefWork:
    status: str
    message_type: str
    message_version: str
    message: CrossrefWorkMessage


def _first(values: list[str] | None) -> str | None:
    if not values:
        return None
    return next((value for value in values if value), None)


@lru_cache()
def get_crossref_work_by_doi(doi: str) -> CrossrefWork | None:
    """Return the Crossref record, or None when Crossref has no such DOI.

    Crossref only mints records for its own members, so a None here is routine
    for arXiv, DataCite and PMLR identifiers rather than an error.
    """
    logger.info(f"fetching Crossref info for doi {doi}")
    endpoint = f"{get_crossref_request_endpoint_template()}/works/{doi}"
    payload = fetch_json(endpoint, provider="crossref")
    if payload is None:
        return None
    return CrossrefWork(**dekebabize(payload))
