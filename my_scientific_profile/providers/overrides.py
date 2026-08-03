import datetime as dt
import logging

from my_scientific_profile.config.config import find_paper_config
from my_scientific_profile.papers.venue import VenueKind
from my_scientific_profile.papers.work_id import WorkId
from my_scientific_profile.providers.base import PartialRecord

__all__ = ["ConfigProvider"]

logger = logging.getLogger(__name__)

# Venue fields may be given either at the top level or nested under `venue`.
VENUE_KEYS = {
    "kind": "venue_kind",
    "name": "venue_name",
    "abbreviation": "venue_abbreviation",
    "volume": "volume",
    "issue": "issue",
    "pages": "pages",
    "url": "url",
}

PLAIN_KEYS = ("title", "abstract", "tldr", "bib_entry")


class ConfigProvider:
    """Hand-written overrides from the config file, which outrank every API.

    This is the escape hatch for a venue no indexer covers yet: a conference
    whose proceedings have not been published, or a repository nobody names
    properly. Entries are meant to be deleted once the providers catch up,
    which they can be without touching any code.
    """

    name = "config"

    def supports(self, work_id: WorkId) -> bool:
        return bool(self._entry(work_id))

    def fetch(self, work_id: WorkId) -> PartialRecord | None:
        entry = self._entry(work_id)
        if not entry:
            return None
        values = {}
        for key in PLAIN_KEYS:
            if entry.get(key):
                values[key] = entry[key]
        venue = dict(entry.get("venue") or {})
        for source_key, field in VENUE_KEYS.items():
            if venue.get(source_key) is not None:
                values[field] = venue[source_key]
        if values.get("venue_kind"):
            values["venue_kind"] = _venue_kind(values["venue_kind"], work_id)
        if date := entry.get("publication_date"):
            values["publication_date"] = _publication_date(date, work_id)
        for field in ("volume", "issue", "pages"):
            if values.get(field) is not None:
                values[field] = str(values[field])
        if not values:
            return None
        return PartialRecord(provider=self.name, **values)

    def _entry(self, work_id: WorkId) -> dict:
        return find_paper_config(doi=work_id.doi, work_key=work_id.key)


def _venue_kind(raw, work_id: WorkId) -> VenueKind | None:
    if isinstance(raw, VenueKind):
        return raw
    try:
        return VenueKind(str(raw).strip().lower())
    except ValueError:
        logger.warning(
            f"config gives {work_id.key} an unknown venue kind {raw!r}; "
            f"expected one of {[k.value for k in VenueKind]}"
        )
        return None


def _publication_date(raw, work_id: WorkId) -> dt.datetime | None:
    if isinstance(raw, dt.datetime):
        return raw
    if isinstance(raw, dt.date):
        return dt.datetime(raw.year, raw.month, raw.day)
    try:
        return dt.datetime.fromisoformat(str(raw))
    except ValueError:
        logger.warning(f"config gives {work_id.key} an unreadable date {raw!r}")
        return None
