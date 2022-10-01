from functools import lru_cache

from pydantic import parse_obj_as
from pydantic.dataclasses import dataclass

from my_scientific_profile.orcid.utils import (
    ExternalIdCollection,
    OrcidDate,
    Source,
    get_orcid_query,
)

__all__ = [
    "OrcidEmployment",
    "OrcidOrganization",
    "fetch_employment_for_orcid_id",
    "get_last_organization",
]


@dataclass(frozen=True)
class OrcidAddress:
    city: str
    region: str
    country: str


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
    start_date: OrcidDate = None
    end_date: OrcidDate = None
    role_title: str = None
    department_name: str = None
    url: str = None


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
    last_modified_date: OrcidDate = None
    affiliation_group: list[OrcidAffiliationGroup] = None


@lru_cache
def fetch_employment_for_orcid_id(orcid_id: str) -> OrcidEmployment:
    record = get_orcid_query("employments", orcid_id=orcid_id, suffix=None)
    return parse_obj_as(OrcidEmployment, record)


def get_last_organization(employment: OrcidEmployment) -> OrcidOrganization | None:
    try:
        return (
            employment.affiliation_group[0].summaries[0].employment_summary.organization
        )
    except (KeyError, TypeError, IndexError):
        return None
