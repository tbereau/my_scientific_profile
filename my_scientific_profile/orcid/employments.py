import logging
from functools import lru_cache

from pydantic.dataclasses import dataclass

from my_scientific_profile.orcid.utils import (
    ExternalIdCollection,
    OrcidDate,
    Source,
    UrlValue,
    get_orcid_query,
)

__all__ = [
    "OrcidEmployment",
    "OrcidOrganization",
    "fetch_employment_for_orcid_id",
    "get_last_organization",
]

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OrcidAddress:
    country: str
    city: str | None = None
    region: str | None = None


@dataclass(frozen=True)
class OrcidOrganization:
    name: str
    address: OrcidAddress


@dataclass(frozen=True)
class OrcidEmploymentSummary:
    created_date: OrcidDate
    last_modified_date: OrcidDate
    source: Source
    put_code: int
    organization: OrcidOrganization
    start_date: OrcidDate | None = None
    end_date: OrcidDate | None = None
    role_title: str | None = None
    department_name: str | None = None
    url: UrlValue | None = None


@dataclass(frozen=True)
class OrcidEmploymentSummaryCollection:
    employment_summary: OrcidEmploymentSummary


@dataclass(frozen=True)
class OrcidAffiliationGroup:
    last_modified_date: OrcidDate
    external_ids: ExternalIdCollection
    summaries: list[OrcidEmploymentSummaryCollection]


@dataclass(frozen=True)
class OrcidEmployment:
    path: str
    last_modified_date: OrcidDate | None = None
    affiliation_group: list[OrcidAffiliationGroup] | None = None


@lru_cache
def fetch_employment_for_orcid_id(orcid_id: str) -> OrcidEmployment:
    record = get_orcid_query("employments", orcid_id=orcid_id, suffix=None)
    return OrcidEmployment(**record)


def get_last_organization(employment: OrcidEmployment) -> OrcidOrganization | None:
    try:
        return (
            employment.affiliation_group[0].summaries[0].employment_summary.organization
        )
    except (KeyError, TypeError, IndexError):
        return None
