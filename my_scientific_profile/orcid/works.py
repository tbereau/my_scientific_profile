from dataclasses import dataclass, field
from typing import Dict, List, Optional

from dataclass_wizard import JSONSerializable

from my_scientific_profile.orcid.detailed_work import (
    ExternalIdCollection,
    ExternalIds,
    OrcidDetailedWork,
    PublicationDate,
    Source,
    Title,
    TitleField,
    get_detailed_work,
)
from my_scientific_profile.orcid.utils import OrcidDate, get_orcid_query

__all__ = [
    "OrcidWorks",
    "OrcidWork",
    "ExternalIds",
    "WorkSummary",
    "get_put_code_to_doi_map",
    "get_doi_to_put_code_map",
    "get_works",
    "get_all_detailed_works",
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
    response = get_orcid_query("works")
    return OrcidWorks.from_dict(response)


def get_doi_to_put_code_map() -> Dict[str, int]:
    works = get_works()
    work_summaries = [
        summary for work_group in works.group for summary in work_group.work_summary
    ]
    return {
        val.external_ids.external_id[0].external_id_value: key.put_code
        for key, val in zip(work_summaries, work_summaries)
    }


def get_put_code_to_doi_map() -> Dict[str, int]:
    works = get_works()
    work_summaries = [
        summary for work_group in works.group for summary in work_group.work_summary
    ]
    return {
        key.put_code: val.external_ids.external_id[0].external_id_value
        for key, val in zip(work_summaries, work_summaries)
    }


def get_all_detailed_works() -> List[OrcidDetailedWork]:
    doi_to_put_code_map = get_doi_to_put_code_map()
    return [get_detailed_work(put_code) for put_code in doi_to_put_code_map.values()]
