"""Finding works that belong on the record but are not on it.

The reason a missing paper goes unnoticed is that nothing looks for one. ORCID
stays the authority on what counts as one's own work — it is curated, and an
automatic feed would drag in datasets, duplicate preprints and the published
twin of every posting. But OpenAlex will happily say what it attributes to an
ORCID, and the difference is worth reading now and then.
"""

import logging
from dataclasses import dataclass

from my_scientific_profile.config.config import (
    get_configured_work_keys,
    get_ignored_work_keys,
    get_my_orcid,
)
from my_scientific_profile.orcid.works import get_work_id_to_put_code_map
from my_scientific_profile.papers.venue import VenueKind
from my_scientific_profile.papers.work_id import WorkId
from my_scientific_profile.providers.openalex import (
    OPENALEX_VENUE_KINDS,
    reconstruct_abstract,
)
from my_scientific_profile.utils.http import fetch_json
from my_scientific_profile.utils.text import titles_match

__all__ = ["UnlistedWork", "find_unlisted_works"]

logger = logging.getLogger(__name__)

OPENALEX_ENDPOINT = "https://api.openalex.org"
PAGE_SIZE = 200

# Kinds worth being told about. Preprints count: a conference paper whose
# proceedings are not out yet looks exactly like one, which is the case this
# report exists to catch. Datasets and software are normally left off a
# publication list on purpose.
KINDS_WORTH_REPORTING = (
    VenueKind.JOURNAL,
    VenueKind.CONFERENCE,
    VenueKind.BOOK,
    VenueKind.PREPRINT,
)


@dataclass(frozen=True)
class UnlistedWork:
    work_id: WorkId
    title: str
    venue: str | None
    year: int | None
    kind: VenueKind | None

    def __str__(self) -> str:
        venue = self.venue or "unknown venue"
        return f"{self.work_id.key} — {self.title} ({venue}, {self.year})"


def find_unlisted_works(
    orcid_id: str = None, include_datasets: bool = False
) -> list[UnlistedWork]:
    """Works OpenAlex attributes to this ORCID that the record does not list.

    Titles are compared as well as identifiers, so the published version of
    something already listed as a preprint is not reported as missing.
    """
    orcid_id = orcid_id or get_my_orcid()
    listed = set(get_work_id_to_put_code_map(orcid_id))
    listed |= {WorkId.parse(key) for key in get_configured_work_keys()}
    ignored = get_ignored_work_keys()
    listed_dois = {work_id.doi for work_id in listed if work_id.doi}

    unlisted = []
    for work in _works_for_orcid(orcid_id):
        doi = _bare_doi(work.get("doi"))
        if not doi:
            continue
        work_id = WorkId.from_doi(doi)
        if work_id in listed or doi in listed_dois:
            continue
        if doi in ignored or work_id.key in ignored:
            continue
        kind = OPENALEX_VENUE_KINDS.get((work.get("type") or "").lower())
        if not include_datasets and kind not in KINDS_WORTH_REPORTING:
            continue
        title = work.get("title") or ""
        if not title:
            continue
        unlisted.append(
            UnlistedWork(
                work_id=work_id,
                title=title,
                venue=(
                    ((work.get("primary_location") or {}).get("source") or {})
                ).get("display_name"),
                year=work.get("publication_year"),
                kind=kind,
            )
        )
    return _drop_titles_already_listed(unlisted, orcid_id)


def _drop_titles_already_listed(
    candidates: list[UnlistedWork], orcid_id: str
) -> list[UnlistedWork]:
    """Remove candidates that are another version of something already listed."""
    from my_scientific_profile.papers.papers import fetch_all_paper_infos

    listed_titles = [paper.title for paper in fetch_all_paper_infos(orcid_id)]
    remaining = []
    for candidate in candidates:
        if any(titles_match(candidate.title, title) for title in listed_titles):
            logger.info(f"{candidate.work_id.key} is already listed under another id")
            continue
        remaining.append(candidate)
    return remaining


def _works_for_orcid(orcid_id: str) -> list[dict]:
    from my_scientific_profile.config.config import get_email_address

    payload = fetch_json(
        f"{OPENALEX_ENDPOINT}/works"
        f"?filter=author.orcid:{orcid_id}"
        f"&per-page={PAGE_SIZE}"
        f"&select=id,doi,title,type,publication_year,primary_location"
        f"&mailto={get_email_address()}",
        provider="openalex",
    )
    return (payload or {}).get("results") or []


def _bare_doi(doi: str | None) -> str | None:
    if not doi:
        return None
    return doi.removeprefix("https://doi.org/").removeprefix("http://doi.org/") or None
