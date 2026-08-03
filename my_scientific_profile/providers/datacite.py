import datetime as dt
import logging

from my_scientific_profile.papers.venue import VenueKind
from my_scientific_profile.papers.work_id import WorkId
from my_scientific_profile.providers.base import AuthorRef, PartialRecord
from my_scientific_profile.utils.http import fetch_json

__all__ = ["DataCiteProvider"]

logger = logging.getLogger(__name__)

DATACITE_ENDPOINT = "https://api.datacite.org/dois"

DATACITE_VENUE_KINDS = {
    "preprint": VenueKind.PREPRINT,
    "software": VenueKind.REPOSITORY,
    "dataset": VenueKind.REPOSITORY,
    "text": VenueKind.REPOSITORY,
    "journalarticle": VenueKind.JOURNAL,
    "conferencepaper": VenueKind.CONFERENCE,
    "conferenceproceeding": VenueKind.CONFERENCE,
    "book": VenueKind.BOOK,
    "bookchapter": VenueKind.BOOK,
}


class DataCiteProvider:
    """DataCite, the registration agency behind arXiv and Zenodo DOIs.

    These DOIs are the reason a Crossref-only pipeline cannot see preprints,
    datasets or software, however well formed the identifier looks.
    """

    name = "datacite"

    def supports(self, work_id: WorkId) -> bool:
        return work_id.doi is not None

    def should_fetch(self, work_id: WorkId, collected: dict) -> bool:
        """Only worth asking when Crossref has not already described the work.

        The two agencies partition the DOI space, so for a Crossref member's
        article this would be a guaranteed 404 on every paper.
        """
        return "crossref" not in collected

    def fetch(self, work_id: WorkId) -> PartialRecord | None:
        payload = fetch_json(
            f"{DATACITE_ENDPOINT}/{work_id.doi}", provider="datacite"
        )
        if not payload or "data" not in payload:
            return None
        attributes = payload["data"].get("attributes") or {}
        return PartialRecord(
            provider=self.name,
            title=_title(attributes),
            venue_kind=_venue_kind(attributes),
            venue_name=attributes.get("publisher") or None,
            url=attributes.get("url") or None,
            publication_date=_publication_date(attributes),
            authors=_authors(attributes),
            citation_count=attributes.get("citationCount"),
            abstract=_abstract(attributes),
        )


def _title(attributes: dict) -> str | None:
    for title in attributes.get("titles") or []:
        if value := (title.get("title") or "").strip():
            return value
    return None


def _venue_kind(attributes: dict) -> VenueKind | None:
    types = attributes.get("types") or {}
    for key in ("resourceType", "resourceTypeGeneral"):
        raw = (types.get(key) or "").replace(" ", "").replace("-", "").lower()
        if kind := DATACITE_VENUE_KINDS.get(raw):
            return kind
    return None


def _publication_date(attributes: dict) -> dt.datetime | None:
    # Prefer the issue date; arXiv also lists submission and update dates per
    # version, which say when a revision landed rather than when it came out.
    by_type = {}
    for entry in attributes.get("dates") or []:
        by_type.setdefault((entry.get("dateType") or "").lower(), entry.get("date"))
    for date_type in ("issued", "available", "submitted", "created"):
        if parsed := _parse_date(by_type.get(date_type)):
            return parsed
    year = attributes.get("publicationYear")
    return dt.datetime(int(year), 1, 1) if year else None


def _parse_date(raw: str | None) -> dt.datetime | None:
    if not raw:
        return None
    text = raw.rstrip("Z")
    for suffix in ("", "-01", "-01-01"):
        try:
            return dt.datetime.fromisoformat(text + suffix)
        except ValueError:
            continue
    return None


def _authors(attributes: dict) -> tuple[AuthorRef, ...] | None:
    authors = []
    for creator in attributes.get("creators") or []:
        family = creator.get("familyName")
        if not family:
            continue
        orcid = next(
            (
                identifier.get("nameIdentifier")
                for identifier in creator.get("nameIdentifiers") or []
                if (identifier.get("nameIdentifierScheme") or "").upper() == "ORCID"
            ),
            None,
        )
        authors.append(
            AuthorRef(
                family=family,
                given=creator.get("givenName") or "",
                orcid=_bare_orcid(orcid),
                affiliation=_affiliation_name(creator.get("affiliation") or []),
            )
        )
    return tuple(authors) or None


def _bare_orcid(orcid: str | None) -> str | None:
    if not orcid:
        return None
    return orcid.rsplit("/", 1)[-1] or None


def _affiliation_name(affiliations: list) -> str | None:
    if not affiliations:
        return None
    first = affiliations[0]
    return first.get("name") if isinstance(first, dict) else str(first)


def _abstract(attributes: dict) -> str | None:
    for description in attributes.get("descriptions") or []:
        if (description.get("descriptionType") or "").lower() == "abstract":
            if value := (description.get("description") or "").strip():
                return value
    return None
