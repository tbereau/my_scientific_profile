from __future__ import annotations

import datetime as dt
import logging

from pydantic import field_validator
from pydantic.dataclasses import dataclass
from requests import get

from my_scientific_profile.config.config import get_email_address

logger = logging.getLogger(__name__)

EMAIL_ADDRESS = get_email_address()


@dataclass(frozen=True)
class UnpaywallAffiliation:
    name: str


@dataclass(frozen=True)
class UnpaywallAuthor:
    given: str | None = None
    family: str | None = None
    sequence: str | None = None
    raw_name: str | None = None
    affiliation: list[UnpaywallAffiliation] | None = None

    class Config:
        extra = "ignore"


@dataclass(frozen=True)
class UnpaywallOALocation:
    url: str
    url_for_landing_page: str
    evidence: str
    host_type: str
    is_best: bool
    updated: dt.datetime | None = None
    url_for_pdf: str | None = None
    license: str | None = None
    pmh_id: str | None = None
    endpoint_id: str | None = None
    repository_institution: str | None = None
    oa_date: dt.datetime | None = None
    version: str | None = None

    class Config:
        json_encoders = {
            dt.datetime: lambda v: v.isoformat(),
        }
        extra = "ignore"

    @field_validator("updated", "oa_date", mode="before")
    def time_validate(cls, v):
        if v is not None:
            return dt.datetime.fromisoformat(v)

    @field_validator("updated", "oa_date", mode="before")
    def time_validate(cls, v):
        if v in (None, "", "deprecated"):
            return None
        if isinstance(v, str):
            s = v.strip()
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            try:
                return dt.datetime.fromisoformat(s)
            except ValueError:
                return None
        return v


@dataclass(frozen=True)
class UnpaywallWork:
    doi: str
    doi_url: str
    title: str
    genre: str
    is_paratext: bool
    published_date: str
    year: int
    journal_name: str
    journal_issns: str
    journal_issn_l: str
    journal_is_oa: bool
    journal_is_in_doaj: bool
    is_oa: bool
    oa_status: str
    has_repository_copy: bool
    updated: dt.datetime | None
    z_authors: list[UnpaywallAuthor]
    best_oa_location: UnpaywallOALocation | None = None
    first_oa_location: UnpaywallOALocation | None = None
    oa_locations: list[UnpaywallOALocation] | None = None

    @field_validator("updated", mode="before")
    def work_time_validate(cls, v):
        if v in (None, "", "deprecated"):
            return None
        if isinstance(v, str):
            s = v.strip()
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            try:
                return dt.datetime.fromisoformat(s)
            except ValueError:
                return None
        return v


def get_unpaywall_work_by_doi(doi: str) -> UnpaywallWork:
    endpoint = f"https://api.unpaywall.org/v2/{doi}?email={EMAIL_ADDRESS}"
    logger.info(f"url {endpoint}")
    response = get(endpoint)
    assert (
        response.status_code == 200
    ), f"unexpected status code {response.status_code}: {response.text}"
    return UnpaywallWork(**response.json())
