from dataclasses import dataclass, field
from typing import List, Optional

from dataclass_wizard import JSONSerializable

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
class OrcidEmployment(JSONSerializable):
    last_modified_date: Optional[OrcidDate]
    affiliation_group: List["OrcidAffiliationGroup"]
    path: str


@dataclass(frozen=True)
class OrcidAffiliationGroup(JSONSerializable):
    last_modified_date: OrcidDate
    external_ids: ExternalIdCollection
    summaries: List["OrcidEmploymentSummaryCollection"]


@dataclass(frozen=True)
class OrcidEmploymentSummaryCollection(JSONSerializable):
    employment_summary: "OrcidEmploymentSummary"


@dataclass(frozen=True)
class OrcidEmploymentSummary(JSONSerializable):
    created_date: OrcidDate
    last_modified_date: OrcidDate
    source: Source
    put_code: int
    organization: "OrcidOrganization"
    start_date: OrcidDate
    end_date: Optional[OrcidDate] = field(default=None)
    role_title: Optional[str] = field(default=None)
    department_name: Optional[str] = field(default=None)
    url: Optional[str] = field(default=None)


@dataclass(frozen=True)
class OrcidOrganization(JSONSerializable):
    name: str
    address: "OrcidAddress"


@dataclass(frozen=True)
class OrcidAddress(JSONSerializable):
    city: str
    region: str
    country: str


def fetch_employment_for_orcid_id(orcid_id: str) -> OrcidEmployment:
    record = get_orcid_query("employments", orcid_id=orcid_id, suffix=None)
    return OrcidEmployment.from_dict(record)


def get_last_organization(employment: OrcidEmployment) -> Optional[OrcidOrganization]:
    try:
        return (
            employment.affiliation_group[0].summaries[0].employment_summary.organization
        )
    except (KeyError, IndexError):
        return None
