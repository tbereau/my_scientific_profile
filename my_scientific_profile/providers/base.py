import datetime as dt
from dataclasses import dataclass, fields
from typing import Protocol, runtime_checkable

from my_scientific_profile.papers.open_access import OpenAccessPaperInfo
from my_scientific_profile.papers.venue import VenueKind
from my_scientific_profile.papers.work_id import WorkId

__all__ = [
    "AuthorRef",
    "PartialRecord",
    "MetadataProvider",
    "RECORD_FIELDS",
    "build_authors",
    "split_display_name",
]


@dataclass(frozen=True)
class AuthorRef:
    """An author as a provider reports them, before any lookup.

    Providers hand back names rather than Author objects because turning a name
    into an Author costs an ORCID search, and only the provider that wins the
    authors field is worth paying for.
    """

    family: str
    given: str = ""
    orcid: str | None = None
    affiliation: str | None = None


@dataclass(frozen=True)
class PartialRecord:
    """What one provider knows about a work. Everything is optional.

    No single provider covers every field: Crossref has no TL;DR, DBLP has no
    abstract, and DataCite has no citation count. The merge step decides which
    provider wins each field rather than making any one of them authoritative.
    """

    provider: str
    title: str | None = None
    venue_kind: VenueKind | None = None
    venue_name: str | None = None
    venue_abbreviation: str | None = None
    volume: str | None = None
    issue: str | None = None
    pages: str | None = None
    url: str | None = None
    publication_date: dt.datetime | None = None
    authors: tuple[AuthorRef, ...] | None = None
    citation_count: int | None = None
    abstract: str | None = None
    tldr: str | None = None
    bib_entry: str | None = None
    open_access: OpenAccessPaperInfo | None = None


# Every field a provider can contribute, i.e. all but its own name.
RECORD_FIELDS = tuple(f.name for f in fields(PartialRecord) if f.name != "provider")


@runtime_checkable
class MetadataProvider(Protocol):
    name: str

    def supports(self, work_id: WorkId) -> bool:
        """Whether this provider could hold the work at all."""

    def fetch(self, work_id: WorkId) -> PartialRecord | None:
        """The provider's view of the work, or None if it holds no record.

        Raise ProviderUnavailable when the service itself fails: returning None
        asserts that the work is absent, which an outage cannot establish.
        """


def build_authors(refs: tuple[AuthorRef, ...] | None) -> list:
    """Turn the winning provider's author references into Author objects.

    Everything routes through CrossrefAuthor so there is one path for ORCID
    enrichment, config name fixes and singleton merging: the same person found
    via OpenAlex deduplicates against the one found via Crossref.
    """
    from my_scientific_profile.authors.authors import get_author_from_orcid_or_crossref
    from my_scientific_profile.crossref.utils import (
        CrossrefAffiliation,
        CrossrefAuthor,
    )

    authors = []
    for ref in refs or ():
        if not ref.family:
            continue
        authors.append(
            get_author_from_orcid_or_crossref(
                CrossrefAuthor(
                    given=ref.given or "",
                    family=ref.family,
                    sequence="additional",
                    affiliation=(
                        [CrossrefAffiliation(ref.affiliation)]
                        if ref.affiliation
                        else []
                    ),
                    orcid=ref.orcid,
                )
            )
        )
    return authors


def split_display_name(display_name: str) -> tuple[str, str]:
    """Split "Sander Hummerich" into given and family names.

    Providers that only publish a display name leave no better option; the
    result feeds the same ORCID lookup as any other author.
    """
    parts = (display_name or "").split()
    if len(parts) < 2:
        return "", (parts[0] if parts else "")
    return " ".join(parts[:-1]), parts[-1]
