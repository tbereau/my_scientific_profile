import datetime as dt
import logging

from pydantic import parse_obj_as, validator
from pydantic.dataclasses import dataclass
from requests import get

logger = logging.getLogger(__name__)

EMAIL_ADDRESS = "tristan.bereau@gmail.com"


@dataclass(frozen=True)
class UnpaywallAffiliation:
    name: str


@dataclass(frozen=True)
class UnpaywallAuthor:
    given: str
    family: str
    sequence: str
    affiliation: list[UnpaywallAffiliation] = None


@dataclass(frozen=True)
class UnpaywallOALocation:
    url: str
    url_for_landing_page: str
    evidence: str
    host_type: str
    is_best: bool
    updated: dt.datetime = None
    url_for_pdf: str = None
    license: str = None
    pmh_id: str = None
    endpoint_id: str = None
    repository_institution: str = None
    oa_date: dt.datetime = None
    version: str = None

    class Config:
        json_encoders = {
            dt.datetime: lambda v: v.isoformat(),
        }

    @validator("updated", "oa_date", pre=True)
    def time_validate(cls, v):
        if v is not None:
            return dt.datetime.fromisoformat(v)


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
    updated: dt.datetime
    z_authors: list[UnpaywallAuthor]
    best_oa_location: UnpaywallOALocation = None
    first_oa_location: UnpaywallOALocation = None
    oa_locations: list[UnpaywallOALocation] = None


def get_unpaywall_work_by_doi(doi: str) -> UnpaywallWork:
    endpoint = f"https://api.unpaywall.org/v2/{doi}?email={EMAIL_ADDRESS}"
    response = get(endpoint)
    assert (
        response.status_code == 200
    ), f"unexpected status code {response.status_code}: {response.text}"
    return parse_obj_as(UnpaywallWork, response.json())
