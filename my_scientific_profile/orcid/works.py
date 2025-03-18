from functools import lru_cache
from typing import Dict, Optional

from humps import dekebabize
from pydantic.dataclasses import dataclass

from my_scientific_profile.orcid.detailed_work import (
    ExternalIdCollection,
    ExternalIds,
    OrcidDetailedWork,
    PublicationDate,
    Title,
    TitleField,
    get_detailed_work,
)
from my_scientific_profile.orcid.utils import (
    OrcidDate,
    Source,
    UrlValue,
    get_orcid_query,
)

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
class WorkSummary:
    put_code: int
    created_date: OrcidDate
    last_modified_date: OrcidDate
    source: Source
    title: TitleField
    external_ids: ExternalIdCollection
    type: str
    visibility: str
    path: str
    display_index: int
    url: Optional[UrlValue] = None
    journal_title: Optional[Title] = None
    publication_date: Optional[PublicationDate] = None


@dataclass(frozen=True)
class OrcidWork:
    last_modified_date: OrcidDate
    external_ids: ExternalIdCollection
    work_summary: list[WorkSummary]


@dataclass(frozen=True)
class OrcidWorks:
    group: list[OrcidWork]
    path: str
    last_modified_date: OrcidDate = None


@lru_cache
def get_works(orcid_id: str = None) -> OrcidWorks:
    response = get_orcid_query("works", orcid_id=orcid_id)
    return OrcidWorks(**dekebabize(response))


@lru_cache
def get_doi_to_put_code_map(orcid_id: str = None) -> Dict[str, int]:
    works = get_works(orcid_id)
    work_summaries = [
        summary for work_group in works.group for summary in work_group.work_summary
    ]
    return {
        val.external_ids.external_id[0].external_id_value: key.put_code
        for key, val in zip(work_summaries, work_summaries)
    }


@lru_cache
def get_put_code_to_doi_map(orcid_id: str = None) -> Dict[str, int]:
    works = get_works(orcid_id)
    work_summaries = [
        summary for work_group in works.group for summary in work_group.work_summary
    ]
    return {
        key.put_code: val.external_ids.external_id[0].external_id_value
        for key, val in zip(work_summaries, work_summaries)
    }


@lru_cache
def get_all_detailed_works() -> list[OrcidDetailedWork]:
    doi_to_put_code_map = get_doi_to_put_code_map()
    return [get_detailed_work(put_code) for put_code in doi_to_put_code_map.values()]
