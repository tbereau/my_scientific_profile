import logging
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
    get_my_orcid,
)
from my_scientific_profile.papers.work_id import RESOLVABLE_ID_TYPES, WorkId

__all__ = [
    "OrcidWorks",
    "OrcidWork",
    "ExternalIds",
    "WorkSummary",
    "get_put_code_to_doi_map",
    "get_doi_to_put_code_map",
    "get_work_id_to_put_code_map",
    "get_works",
    "get_all_detailed_works",
]

logger = logging.getLogger(__name__)


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
    if not orcid_id:
        orcid_id = get_my_orcid()
    response = get_orcid_query("works", orcid_id=orcid_id)
    return OrcidWorks(**dekebabize(response))


def _work_summaries(orcid_id: str = None) -> list[WorkSummary]:
    works = get_works(orcid_id)
    return [
        summary for work_group in works.group for summary in work_group.work_summary
    ]


def _work_id_for_summary(summary: WorkSummary) -> WorkId | None:
    """Pick the most resolvable identifier ORCID lists for a work.

    Never take the first identifier blindly: ORCID also reports Scopus eids and
    PMIDs, and for anything published outside a Crossref member there may be no
    DOI at all, only an arXiv id.
    """
    external_ids = summary.external_ids.external_id or []
    by_type = {}
    for external_id in external_ids:
        by_type.setdefault(
            (external_id.external_id_type or "").lower(), external_id
        )
    for id_type in RESOLVABLE_ID_TYPES:
        if external_id := by_type.get(id_type):
            value = external_id.external_id_value
            if work_id := WorkId.from_external_id(id_type, value):
                return work_id
    logger.info(
        f"no resolvable identifier for '{summary.title.title.value}' "
        f"(has {sorted(by_type)})"
    )
    return None


@lru_cache
def get_work_id_to_put_code_map(orcid_id: str = None) -> Dict[WorkId, int]:
    result = {}
    for summary in _work_summaries(orcid_id):
        if work_id := _work_id_for_summary(summary):
            result.setdefault(work_id, summary.put_code)
    return result


@lru_cache
def get_doi_to_put_code_map(orcid_id: str = None) -> Dict[str, int]:
    return {
        work_id.doi: put_code
        for work_id, put_code in get_work_id_to_put_code_map(orcid_id).items()
        if work_id.doi
    }


@lru_cache
def get_put_code_to_doi_map(orcid_id: str = None) -> Dict[int, str]:
    return {
        put_code: doi for doi, put_code in get_doi_to_put_code_map(orcid_id).items()
    }


@lru_cache
def get_all_detailed_works() -> list[OrcidDetailedWork]:
    put_codes = get_work_id_to_put_code_map().values()
    works = [get_detailed_work(put_code) for put_code in put_codes]
    return [work for work in works if work is not None]
