import logging
import re
from urllib.parse import quote

from my_scientific_profile.papers.venue import VenueKind
from my_scientific_profile.papers.work_id import WorkId
from my_scientific_profile.providers.base import PartialRecord
from my_scientific_profile.utils.http import fetch_json
from my_scientific_profile.utils.text import title_similarity, titles_match

__all__ = ["DblpProvider"]

logger = logging.getLogger(__name__)

DBLP_ENDPOINT = "https://dblp.org/search/publ/api"
MAX_HITS = 10

# DBLP files the arXiv copy of a paper under CoRR as an informal publication.
# That is the record we already have; the proceedings entry is what we want.
INFORMAL_TYPE = "informal and other publications"
DBLP_VENUE_KINDS = {
    "conference and workshop papers": VenueKind.CONFERENCE,
    "journal articles": VenueKind.JOURNAL,
    "books and theses": VenueKind.BOOK,
    "parts in books or collections": VenueKind.BOOK,
}

_PMLR_VOLUME = re.compile(r"proceedings\.mlr\.press/v(\d+)", re.I)


class DblpProvider:
    """DBLP, the computer science bibliography.

    It is the only machine-readable source that names a machine learning
    conference correctly: PMLR proceedings carry no DOI, so Crossref cannot
    describe them and OpenAlex indexes almost none of them.

    Consulted only when the other providers leave a work looking unpublished,
    both to save a request per paper and because a title search against a
    bibliography of another field invites false matches.
    """

    name = "dblp"

    def supports(self, work_id: WorkId) -> bool:
        # Never queried by identifier: DBLP has no DOI lookup worth using.
        return False

    def should_refine(self, work_id: WorkId, merged: PartialRecord) -> bool:
        if not merged.title:
            return False
        return merged.venue_kind in (None, VenueKind.PREPRINT, VenueKind.REPOSITORY)

    def refine(self, work_id: WorkId, merged: PartialRecord) -> PartialRecord | None:
        hit = self._best_hit(merged.title)
        if hit is None:
            return None
        venue = hit.get("venue")
        if isinstance(venue, list):
            venue = venue[0] if venue else None
        electronic_edition = hit.get("ee")
        volume = None
        if electronic_edition and (match := _PMLR_VOLUME.search(electronic_edition)):
            volume = match.group(1)
        return PartialRecord(
            provider=self.name,
            venue_kind=DBLP_VENUE_KINDS.get((hit.get("type") or "").lower()),
            venue_name=venue,
            venue_abbreviation=venue,
            volume=volume or hit.get("volume"),
            pages=hit.get("pages"),
            url=electronic_edition,
        )

    def _best_hit(self, title: str) -> dict | None:
        payload = fetch_json(
            f"{DBLP_ENDPOINT}?q={quote(title)}&format=json&h={MAX_HITS}",
            provider="dblp",
        )
        result = (payload or {}).get("result") or {}
        hits = (result.get("hits") or {}).get("hit") or []
        candidates = []
        for entry in hits:
            info = entry.get("info") or {}
            # DBLP ends every title with a full stop.
            hit_title = (info.get("title") or "").rstrip(".")
            if not titles_match(hit_title, title):
                continue
            if (info.get("type") or "").lower() == INFORMAL_TYPE:
                continue
            candidates.append((title_similarity(hit_title, title), info))
        if not candidates:
            logger.info(f"DBLP has no formal publication matching {title[:60]!r}")
            return None
        return max(candidates, key=lambda candidate: candidate[0])[1]
