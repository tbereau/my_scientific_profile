import datetime as dt
from dataclasses import dataclass, field
from typing import List, Optional

import pandas as pd
from dataclass_wizard import JSONSerializable, json_field

import my_scientific_profile.utils  # noqa

__all__ = [
    "CrossrefDate",
    "CrossrefFunder",
    "CrossrefContentDomain",
    "CrossrefAuthor",
    "CrossrefAffiliation",
    "CrossrefReference",
    "CrossrefLink",
    "CrossrefAssertion",
    "get_crossref_request_endpoint_template",
]


@dataclass(frozen=True)
class CrossrefDate(JSONSerializable):
    date_parts: List[List[int]] = field(repr=False)
    timestamp: Optional[int] = field(default=None, repr=False)
    date_time: Optional[dt.datetime] = field(default=None)

    def __post_init__(self):
        if self.date_time is None:
            object.__setattr__(
                self,
                "datetime",
                pd.to_datetime(" ".join(str(x) for x in self.date_parts[0])),
            )


@dataclass(frozen=True)
class CrossrefFunder(JSONSerializable):
    name: str
    DOI: Optional[str] = field(default=None)
    doi_asserted_by: Optional[str] = field(default=None)


@dataclass(frozen=True)
class CrossrefContentDomain(JSONSerializable):
    domain: List[str]
    crossmark_restriction: bool


@dataclass(frozen=True)
class CrossrefAuthor(JSONSerializable):
    given: str
    family: str
    sequence: str
    affiliation: List["CrossrefAffiliation"]
    orcid: Optional[str] = field(default=None)
    authenticated_orcid: Optional[bool] = field(default=None)


@dataclass(frozen=True)
class CrossrefAffiliation(JSONSerializable):
    name: str


@dataclass(frozen=True)
class CrossrefReference(JSONSerializable):
    key: str
    doi: Optional[str] = json_field("DOI", default=None)
    doi_asserted_by: Optional[str] = field(default=None)
    unstructured: Optional[str] = field(default=None)
    first_page: Optional[str] = field(default=None)
    volume_title: Optional[str] = field(default=None)
    author: Optional[str] = field(default=None)
    year: Optional[int] = field(default=None)


@dataclass(frozen=True)
class CrossrefLink(JSONSerializable):
    url: str
    content_type: str
    content_version: str
    intended_application: str


@dataclass(frozen=True)
class CrossrefAssertion(JSONSerializable):
    name: str
    date: str = json_field("value")
    label: Optional[str] = field(default=None)
    order: Optional[int] = field(default=None)


def get_crossref_request_endpoint_template() -> str:
    return f"https://api.crossref.org/v1"
