import datetime as dt
import logging
from functools import lru_cache

import pandas as pd
from humps import dekebabize
from pydantic import Field, parse_obj_as
from pydantic.dataclasses import dataclass

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
    translated_title: str = None


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
    contributor_sequence: str = None


@dataclass(frozen=True)
class Contributor:
    credit_name: StrValue
    contributor_attributes: ContributorAttributes = None
    contributor_email: str = None
    contributor_orcid: SourceClientId | str = None


@dataclass(frozen=True)
class Contributors:
    contributor: list[Contributor]


@dataclass(frozen=True)
class PublicationDate:
    year: IntValue = Field(..., repr=False)
    month: IntValue = Field(repr=False, default=None)
    day: IntValue = Field(repr=False, default=None)

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
    publication_date: PublicationDate
    external_ids: ExternalIdCollection
    contributors: Contributors
    journal_title: Title
    url: StrValue = None
    citation: Citation = None
    language_code: str = None
    country: str = None
    visibility: str = None
    short_description: str = None


@lru_cache
def get_detailed_work(put_code: int) -> OrcidDetailedWork:
    response = get_orcid_query("work", suffix=str(put_code))
    return parse_obj_as(OrcidDetailedWork, dekebabize(response))
