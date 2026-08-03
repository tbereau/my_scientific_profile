from enum import Enum

from pydantic import field_validator
from pydantic.dataclasses import dataclass

__all__ = ["VenueKind", "VenueInfo", "JournalInfo"]


class VenueKind(str, Enum):
    """What sort of place a work appeared in.

    Journals are not the only option: conference proceedings carry no volume or
    issue, and preprints carry no venue name at all.
    """

    JOURNAL = "journal"
    CONFERENCE = "conference"
    PREPRINT = "preprint"
    REPOSITORY = "repository"
    BOOK = "book"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class VenueInfo:
    url: str
    # The default serves records serialised before venues had a kind; every
    # code path that builds a venue passes one explicitly.
    kind: VenueKind = VenueKind.JOURNAL
    name: str | None = None
    issue: str | None = None
    abbreviation: str | None = None
    pages: str | None = None
    volume: str | None = None

    @field_validator("volume", mode="before")
    @classmethod
    def _coerce_volume(cls, value):
        # Volumes are not reliably numeric ("12A", "S1"), but earlier records
        # stored them as ints, which pydantic v2 will not widen to str.
        if value is None or isinstance(value, str):
            return value
        return str(value)


# The attribute on Paper is still called `journal`, so this alias keeps older
# imports working and matches the column names the website reads.
JournalInfo = VenueInfo
