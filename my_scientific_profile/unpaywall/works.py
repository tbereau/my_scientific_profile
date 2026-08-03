from __future__ import annotations

import datetime as dt
import logging
from functools import lru_cache

from pydantic import field_validator
from pydantic.dataclasses import dataclass

from my_scientific_profile.config.config import get_email_address
from my_scientific_profile.utils.http import fetch_json

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
    url: str | None = None
    url_for_landing_page: str | None = None
    evidence: str | None = None
    host_type: str | None = None
    is_best: bool = True
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
    # Only the identifiers are guaranteed. Everything else is absent for one
    # genre or another: preprints carry no ISSN, datasets carry no journal.
    doi: str
    doi_url: str
    title: str | None = None
    genre: str | None = None
    is_paratext: bool = False
    published_date: str | None = None
    year: int | None = None
    journal_name: str | None = None
    journal_issns: str | None = None
    journal_issn_l: str | None = None
    journal_is_oa: bool = False
    journal_is_in_doaj: bool = False
    is_oa: bool = False
    oa_status: str | None = None
    has_repository_copy: bool = False
    updated: dt.datetime | None = None
    z_authors: list[UnpaywallAuthor] | None = None
    best_oa_location: UnpaywallOALocation | None = None
    first_oa_location: UnpaywallOALocation | None = None
    oa_locations: list[UnpaywallOALocation] | None = None

    @field_validator(
        "is_paratext",
        "journal_is_oa",
        "journal_is_in_doaj",
        "is_oa",
        "has_repository_copy",
        mode="before",
    )
    def bool_validate(cls, v):
        return False if v is None else v

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


@lru_cache()
def get_unpaywall_work_by_doi(doi: str) -> UnpaywallWork | None:
    """Return the Unpaywall record, or None when it has no such DOI.

    Unpaywall indexes Crossref DOIs only, so arXiv and DataCite identifiers
    legitimately have no record here.
    """
    endpoint = f"https://api.unpaywall.org/v2/{doi}?email={EMAIL_ADDRESS}"
    logger.info(f"url {endpoint}")
    payload = fetch_json(endpoint, provider="unpaywall")
    if payload is None:
        return None
    return UnpaywallWork(**payload)
