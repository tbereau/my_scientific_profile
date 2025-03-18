import datetime as dt
import logging
from functools import lru_cache
from typing import Optional

import pandas as pd
from humps import dekebabize
from pydantic.dataclasses import dataclass
from pydantic.fields import Field

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
    "Title",
    "TitleField",
    "PublicationDate",
    "get_detailed_work",
]

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Title:
    value: str
    subtitle: str = None
    translated_title: Optional[str] = None


@dataclass(frozen=True)
class TitleField:
    title: Title


@dataclass(frozen=True)
class Citation:
    citation_type: str
    citation_value: str


@dataclass(frozen=True)
class ContributorAttributes:
    contributor_role: str
    contributor_sequence: Optional[str] = None


@dataclass(frozen=True)
class Contributor:
    credit_name: StrValue
    contributor_attributes: Optional[ContributorAttributes] = None
    contributor_email: Optional[str] = None
    contributor_orcid: Optional[SourceClientId | str] = None


@dataclass(frozen=True)
class Contributors:
    contributor: list[Contributor]


@dataclass(frozen=True)
class PublicationDate:
    year: IntValue = Field(..., repr=False)
    month: Optional[IntValue] = Field(repr=False, default=None)
    day: Optional[IntValue] = Field(repr=False, default=None)

    @property
    def datetime(self) -> dt.datetime:
        return pd.to_datetime(
            "-".join(
                [
                    str(x.value)
                    for x in [self.year, self.month, self.day]
                    if x is not None
                ]
            )
        )


@dataclass(frozen=True)
class OrcidDetailedWork:
    put_code: int
    created_date: OrcidDate
    last_modified_date: OrcidDate
    source: Source
    path: str
    title: TitleField
    type: str
    external_ids: ExternalIdCollection
    contributors: Contributors
    journal_title: Optional[Title] = None
    publication_date: Optional[PublicationDate] = None
    url: Optional[StrValue] = None
    citation: Optional[Citation] = None
    language_code: Optional[str] = None
    country: Optional[str] = None
    visibility: Optional[str] = None
    short_description: Optional[str] = None


@lru_cache
def get_detailed_work(put_code: int, orcid_id: str = None) -> OrcidDetailedWork:
    response = get_orcid_query("work", suffix=str(put_code), orcid_id=orcid_id)
    return OrcidDetailedWork(**dekebabize(response))
