import logging

from my_scientific_profile.doi2bib.doi2bib import fetch_bib
from my_scientific_profile.papers.venue import VenueKind
from my_scientific_profile.papers.work_id import WorkId
from my_scientific_profile.providers.base import PartialRecord

__all__ = ["Doi2BibProvider", "render_bib_entry"]

logger = logging.getLogger(__name__)

BIB_ENTRY_TYPES = {
    VenueKind.JOURNAL: "article",
    VenueKind.CONFERENCE: "inproceedings",
    VenueKind.BOOK: "inbook",
    VenueKind.PREPRINT: "misc",
    VenueKind.REPOSITORY: "misc",
}


class Doi2BibProvider:
    """BibTeX by DOI content negotiation, from Crossref or DataCite."""

    name = "doi2bib"

    def supports(self, work_id: WorkId) -> bool:
        return work_id.doi is not None

    def fetch(self, work_id: WorkId) -> PartialRecord | None:
        bib_entry = fetch_bib(work_id.doi)
        if bib_entry is None:
            return None
        return PartialRecord(provider=self.name, bib_entry=bib_entry)


def render_bib_entry(paper) -> str:
    """Compose a BibTeX entry from a resolved paper.

    Content negotiation returns @misc for anything DataCite registered, which
    cites an AISTATS paper as an arXiv posting. Once a work has been resolved,
    the entry is a rendering of what we know rather than a sixth request.
    """
    venue = paper.journal
    entry_type = BIB_ENTRY_TYPES.get(venue.kind, "misc")
    first_author = paper.authors[0].family if paper.authors else "unknown"
    cite_key = f"{first_author}_{paper.year}".replace(" ", "").lower()
    venue_field = "journal" if venue.kind == VenueKind.JOURNAL else "booktitle"
    fields = [
        ("title", paper.title),
        ("author", " and ".join(a.full_name for a in paper.authors)),
        (venue_field, venue.name),
        ("volume", venue.volume),
        ("number", venue.issue),
        ("pages", venue.pages),
        ("year", paper.year),
        ("doi", paper.doi),
        ("url", venue.url),
    ]
    body = ",\n".join(
        f"\t{name} = {{{value}}}" for name, value in fields if value not in (None, "")
    )
    return f"@{entry_type}{{{cite_key},\n{body}\n}}"
