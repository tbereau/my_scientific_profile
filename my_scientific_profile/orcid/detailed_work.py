import datetime as dt
import logging
from dataclasses import dataclass, field
from typing import List, Optional

import pandas as pd
from dataclass_wizard import JSONSerializable, json_field

from my_scientific_profile.orcid.utils import (
    ExternalId,
    ExternalIdCollection,
    ExternalIds,
    IntValue,
    OrcidDate,
    Source,
    SourceClientId,
    StrValue,
    get_orcid_query,
)

__all__ = [
    "OrcidDetailedWork",
    "ExternalId",
    "ExternalIds",
    "ExternalIdCollection",
    "Source",
    "SourceClientId",
    "Title",
    "TitleField",
    "PublicationDate",
    "get_detailed_work",
]

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OrcidDetailedWork(JSONSerializable):
    put_code: int
    created_date: OrcidDate
    last_modified_date: OrcidDate
    source: "Source"
    path: str
    title: "TitleField"
    type: str
    publication_date: "PublicationDate"
    external_ids: "ExternalIdCollection"
    contributors: "Contributors"
    journal_title: "Title"
    url: Optional["StrValue"] = field(default=None)
    citation: Optional["Citation"] = field(default=None)
    language_code: Optional[str] = field(default=None)
    country: Optional[str] = field(default=None)
    visibility: Optional[str] = field(default=None)
    short_description: Optional[str] = field(default=None)


@dataclass(frozen=True)
class Contributors(JSONSerializable):
    contributor: List["Contributor"]


@dataclass(frozen=True)
class Contributor(JSONSerializable):
    credit_name: StrValue
    contributor_attributes: Optional["ContributorAttributes"] = field(default=None)
    contributor_email: Optional[str] = field(default=None)
    contributor_orcid: Optional[str] = field(default=None)


@dataclass(frozen=True)
class ContributorAttributes(JSONSerializable):
    contributor_role: str
    contributor_sequence: Optional[str] = field(default=None)


@dataclass(frozen=True)
class TitleField(JSONSerializable):
    title: "Title"


@dataclass(frozen=True)
class Title(JSONSerializable):
    value: str
    subtitle: Optional[str] = field(default=None)
    translated_title: Optional[str] = field(default=None)


@dataclass(frozen=True)
class PublicationDate(JSONSerializable):
    year: "IntValue" = json_field("year", repr=None)
    month: Optional["IntValue"] = json_field("month", repr=None, default=None)
    day: Optional["IntValue"] = json_field("day", repr=None, default=None)
    datetime: dt.datetime = field(init=False)

    def __post_init__(self):
        datetime = "-".join(
            [str(x.value) for x in [self.year, self.month, self.day] if x is not None]
        )
        object.__setattr__(self, "datetime", pd.to_datetime(datetime))


@dataclass(frozen=True)
class Citation(JSONSerializable):
    citation_type: str
    citation_value: str


def get_detailed_work(put_code: int) -> OrcidDetailedWork:
    response = get_orcid_query("work", suffix=str(put_code))
    return OrcidDetailedWork.from_dict(response)
