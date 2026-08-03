import logging

from my_scientific_profile.crossref.works import get_crossref_work_by_doi
from my_scientific_profile.papers.venue import VenueKind
from my_scientific_profile.papers.work_id import WorkId
from my_scientific_profile.providers.base import AuthorRef, PartialRecord

__all__ = ["CrossrefProvider", "CROSSREF_VENUE_KINDS"]

logger = logging.getLogger(__name__)

CROSSREF_VENUE_KINDS = {
    "journal-article": VenueKind.JOURNAL,
    "proceedings-article": VenueKind.CONFERENCE,
    "proceedings": VenueKind.CONFERENCE,
    "posted-content": VenueKind.PREPRINT,
    "book": VenueKind.BOOK,
    "book-chapter": VenueKind.BOOK,
    "monograph": VenueKind.BOOK,
    "dataset": VenueKind.REPOSITORY,
    "component": VenueKind.REPOSITORY,
}


class CrossrefProvider:
    """Crossref, authoritative for anything its members registered."""

    name = "crossref"

    def supports(self, work_id: WorkId) -> bool:
        # DataCite prefixes are well formed DOIs that Crossref has never heard
        # of, so asking wastes a request per paper.
        return work_id.is_crossref_doi

    def fetch(self, work_id: WorkId) -> PartialRecord | None:
        work = get_crossref_work_by_doi(work_id.doi)
        if work is None:
            return None
        message = work.message
        venue_name = message.venue_name
        kind = CROSSREF_VENUE_KINDS.get(message.type)
        if venue_name is None and kind in (VenueKind.PREPRINT, VenueKind.REPOSITORY):
            # Posted content has no container title; Crossref names the host
            # repository under institution instead.
            venue_name = message.institution_name
        return PartialRecord(
            provider=self.name,
            title=_first(message.title),
            venue_kind=kind,
            venue_name=venue_name,
            venue_abbreviation=message.venue_abbreviation,
            volume=message.volume,
            issue=message.issue,
            pages=message.page,
            url=message.url,
            publication_date=(
                message.created.date_time if message.created else None
            ),
            authors=_authors(message),
            citation_count=message.is_referenced_by_count,
            abstract=message.abstract,
        )


def _first(values: list[str] | None) -> str | None:
    if not values:
        return None
    return next((value.strip() for value in values if value and value.strip()), None)


def _authors(message) -> tuple[AuthorRef, ...] | None:
    if not message.author:
        return None
    return (
        tuple(
            AuthorRef(
                family=author.family,
                given=author.given,
                orcid=author.orcid,
                affiliation=(
                    author.affiliation[0].name if author.affiliation else None
                ),
            )
            for author in message.author
            if author.family
        )
        or None
    )
