import datetime as dt
import logging

from my_scientific_profile.config.config import get_email_address
from my_scientific_profile.papers.open_access import OpenAccessPaperInfo
from my_scientific_profile.papers.venue import VenueKind
from my_scientific_profile.papers.work_id import WorkId
from my_scientific_profile.providers.base import (
    AuthorRef,
    PartialRecord,
    split_display_name,
)
from my_scientific_profile.utils.http import fetch_json

__all__ = ["OpenAlexProvider", "get_openalex_work_by_doi", "reconstruct_abstract"]

logger = logging.getLogger(__name__)

OPENALEX_ENDPOINT = "https://api.openalex.org"

OPENALEX_VENUE_KINDS = {
    "article": VenueKind.JOURNAL,
    "preprint": VenueKind.PREPRINT,
    "book": VenueKind.BOOK,
    "book-chapter": VenueKind.BOOK,
    "dataset": VenueKind.REPOSITORY,
    "software": VenueKind.REPOSITORY,
    "dissertation": VenueKind.BOOK,
}

# OpenAlex describes where a work sits as well as what it is; a repository
# source means the work is only posted, whatever its own type claims.
OPENALEX_SOURCE_KINDS = {
    "journal": VenueKind.JOURNAL,
    "conference": VenueKind.CONFERENCE,
    "repository": VenueKind.PREPRINT,
    "book series": VenueKind.BOOK,
}


def get_openalex_work_by_doi(doi: str) -> dict | None:
    return fetch_json(
        f"{OPENALEX_ENDPOINT}/works/doi:{doi}?mailto={get_email_address()}",
        provider="openalex",
    )


def reconstruct_abstract(inverted_index: dict | None) -> str | None:
    """Rebuild an abstract from OpenAlex's word to positions mapping."""
    if not inverted_index:
        return None
    positions = {
        position: word
        for word, word_positions in inverted_index.items()
        for position in word_positions
    }
    if not positions:
        return None
    return " ".join(positions[key] for key in sorted(positions)) or None


class OpenAlexProvider:
    """OpenAlex, the one source that covers every DOI we can encounter.

    It aggregates Crossref, DataCite and Unpaywall, so it supplies open access
    status, citation counts and author ORCIDs even for works Crossref rejects.
    Its weak spot is conference proceedings: it holds barely any of PMLR.
    """

    name = "openalex"

    def supports(self, work_id: WorkId) -> bool:
        return work_id.doi is not None

    def fetch(self, work_id: WorkId) -> PartialRecord | None:
        payload = get_openalex_work_by_doi(work_id.doi)
        if not payload or payload.get("id") is None:
            return None
        location = payload.get("primary_location") or {}
        source = location.get("source") or {}
        biblio = payload.get("biblio") or {}
        return PartialRecord(
            provider=self.name,
            title=payload.get("title"),
            venue_kind=_venue_kind(payload, source),
            venue_name=source.get("display_name"),
            venue_abbreviation=source.get("abbreviated_title"),
            volume=biblio.get("volume"),
            issue=biblio.get("issue"),
            pages=_pages(biblio),
            url=location.get("landing_page_url"),
            publication_date=_publication_date(payload),
            authors=_authors(payload),
            citation_count=payload.get("cited_by_count"),
            abstract=reconstruct_abstract(payload.get("abstract_inverted_index")),
            open_access=_open_access(payload, location),
        )


def _venue_kind(payload: dict, source: dict) -> VenueKind | None:
    # What the work is beats where it sits: software on Zenodo lives in a
    # repository, but calling it a preprint on that basis would be wrong.
    if kind := OPENALEX_VENUE_KINDS.get((payload.get("type") or "").lower()):
        return kind
    return OPENALEX_SOURCE_KINDS.get((source.get("type") or "").lower())


def _pages(biblio: dict) -> str | None:
    first, last = biblio.get("first_page"), biblio.get("last_page")
    if first and last:
        return f"{first}-{last}"
    return first or last or None


def _publication_date(payload: dict) -> dt.datetime | None:
    raw = payload.get("publication_date")
    if not raw:
        return None
    try:
        return dt.datetime.fromisoformat(raw)
    except ValueError:
        logger.info(f"unparseable OpenAlex date {raw!r}")
        return None


def _authors(payload: dict) -> tuple[AuthorRef, ...] | None:
    authors = []
    for authorship in payload.get("authorships") or []:
        author = authorship.get("author") or {}
        given, family = split_display_name(author.get("display_name") or "")
        if not family:
            continue
        orcid = (author.get("orcid") or "").removeprefix("https://orcid.org/") or None
        institutions = authorship.get("institutions") or []
        authors.append(
            AuthorRef(
                family=family,
                given=given,
                orcid=orcid,
                affiliation=(
                    institutions[0].get("display_name") if institutions else None
                ),
            )
        )
    return tuple(authors) or None


def _open_access(payload: dict, location: dict) -> OpenAccessPaperInfo | None:
    open_access = payload.get("open_access")
    if not open_access:
        return None
    is_oa = bool(open_access.get("is_oa"))
    if not is_oa:
        return OpenAccessPaperInfo(False, None, None, None)
    return OpenAccessPaperInfo(
        True,
        open_access.get("oa_status"),
        location.get("landing_page_url") or open_access.get("oa_url"),
        location.get("pdf_url") or open_access.get("oa_url"),
    )
