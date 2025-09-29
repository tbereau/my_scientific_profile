from __future__ import annotations

import datetime as dt
import logging
from functools import lru_cache
from typing import Optional, List, Any

import pandas as pd
from humps import dekebabize
from pydantic.dataclasses import dataclass
from pydantic.fields import Field
from pydantic import field_validator, ConfigDict

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



def _unwrap_value(v: Any) -> Optional[str]:
    if v is None:
        return None
    if isinstance(v, dict):
        # ORCID style: {"value": "..."} (ignore other keys)
        return (v.get("value") or "").strip() or None
    s = str(v).strip()
    return s or None


@dataclass(frozen=True)
class Title:
    value: str = None
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

    @field_validator("contributor_email", mode="before")
    @classmethod
    def _coerce_email(cls, v):
        return _unwrap_value(v)

    @field_validator("contributor_orcid", mode="before")
    @classmethod
    def _coerce_orcid(cls, v):
        if v is None:
            return None
        if isinstance(v, dict):
            # Common ORCID patterns:
            # {"path": "0000-0002-..."} or {"uri": "https://orcid.org/0000-..."}
            path = v.get("path")
            if path:
                return path
            uri = v.get("uri")
            if uri:
                return uri
        return v


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
