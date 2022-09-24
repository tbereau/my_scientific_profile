from dataclasses import dataclass, field
from typing import List, Optional

from dataclass_wizard import JSONSerializable
from requests import get

from my_scientific_profile.orcid.detailed_work import (
    ExternalIds,
    PublicationDate,
    Source,
    Title,
    TitleField,
)
from my_scientific_profile.orcid.utils import (
    OrcidDate,
    get_orcid_request_endpoint_template,
    get_orcid_request_headers,
)

__all__ = [
    "OrcidWorks",
    "OrcidWork",
    "ExternalIdCollection",
    "ExternalIds",
    "WorkSummary",
]


@dataclass(frozen=True)
class OrcidWorks(JSONSerializable):
    last_modified_date: "OrcidDate"
    group: List["OrcidWork"]
    path: str


@dataclass(frozen=True)
class OrcidWork(JSONSerializable):
    last_modified_date: "OrcidDate"
    external_ids: "ExternalIdCollection"
    work_summary: List["WorkSummary"]


@dataclass(frozen=True)
class ExternalIdCollection(JSONSerializable):
    external_id: List["ExternalIds"]


@dataclass(frozen=True)
class WorkSummary(JSONSerializable):
    put_code: int
    created_date: OrcidDate
    last_modified_date: OrcidDate
    source: "Source"
    title: "TitleField"
    external_ids: "ExternalIdCollection"
    url: str
    type: str
    publication_date: "PublicationDate"
    visibility: str
    path: str
    display_index: int
    journal_title: Optional[Title] = field(default=None)


def get_works() -> OrcidWorks:
    endpoint = f"{get_orcid_request_endpoint_template()}/works"
    response = get(endpoint, headers=get_orcid_request_headers())
    assert (
        response.status_code == 200
    ), f"unexpected status code {response.status_code}: {response.text}"
    return OrcidWorks.from_dict(response.json())
