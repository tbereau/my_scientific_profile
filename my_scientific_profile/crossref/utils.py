import datetime as dt

import pandas as pd
from pydantic import Field
from pydantic.dataclasses import dataclass

from my_scientific_profile.config.config import find_author_in_config

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


@dataclass(eq=True, frozen=True)
class CrossrefDate:
    date_parts: list[list[int]] = Field(..., repr=False)
    timestamp: int = Field(default=None, repr=False)
    date_time: dt.datetime = None

    def __post_init__(self):
        if self.date_time is None:
            object.__setattr__(
                self,
                "datetime",
                pd.to_datetime(" ".join(str(x) for x in self.date_parts[0])),
            )


@dataclass(eq=True, frozen=True)
class CrossrefFunder:
    name: str
    DOI: str = None
    doi_asserted_by: str = None


@dataclass(eq=True, frozen=True)
class CrossrefContentDomain:
    domain: list[str]
    crossmark_restriction: bool


@dataclass(eq=True, frozen=True)
class CrossrefAffiliation:
    name: str


@dataclass(eq=True, frozen=True)
class CrossrefAuthor:
    given: str
    family: str
    sequence: str
    affiliation: list[CrossrefAffiliation]
    orcid: str = None
    authenticated_orcid: bool = None

    def __post_init__(self):
        if self.orcid:
            orcid = self.orcid.removeprefix("http://orcid.org/").removeprefix(
                "https://orcid.org/"
            )
            object.__setattr__(self, "orcid", orcid)
        else:
            author = find_author_in_config(self.given, self.family, self.orcid)
            if author:
                object.__setattr__(self, "given", author["given"])
                object.__setattr__(self, "family", author["family"])
                object.__setattr__(self, "orcid", author["orcid"])


@dataclass(eq=True, frozen=True)
class CrossrefReference:
    key: str
    doi: str = Field(None, alias="DOI")
    doi_asserted_by: str = None
    unstructured: str = None
    first_page: str = None
    volume_title: str = None
    author: str = None
    year: int = None


@dataclass(eq=True, frozen=True)
class CrossrefLink:
    content_type: str
    content_version: str
    intended_application: str
    url: str = None


@dataclass(eq=True, frozen=True)
class CrossrefAssertion:
    name: str
    date: str = Field(None, alias="value")
    label: str = None
    order: int = None


def get_crossref_request_endpoint_template() -> str:
    return "https://api.crossref.org/v1"
