import datetime as dt
import logging
from dataclasses import dataclass, field
from typing import List, Optional

from dataclass_wizard import JSONSerializable
from requests import get

logger = logging.getLogger(__name__)

EMAIL_ADDRESS = "tristan.bereau@gmail.com"


@dataclass(frozen=True)
class UnpaywallWork(JSONSerializable):
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
    z_authors: List["UnpaywallAuthor"]
    best_oa_location: Optional["UnpaywallOALocation"] = field(default=None)
    first_oa_location: Optional["UnpaywallOALocation"] = field(default=None)
    oa_locations: List["UnpaywallOALocation"] = field(default_factory=list)


@dataclass(frozen=True)
class UnpaywallOALocation(JSONSerializable):
    url: str
    url_for_landing_page: str
    evidence: str
    version: str
    host_type: str
    is_best: bool
    updated: Optional[dt.datetime] = field(default=None)
    url_for_pdf: Optional[str] = field(default=None)
    license: Optional[str] = field(default=None)
    pmh_id: Optional[str] = field(default=None)
    endpoint_id: Optional[str] = field(default=None)
    repository_institution: Optional[str] = field(default=None)
    oa_date: Optional[dt.datetime] = field(default=None)


@dataclass(frozen=True)
class UnpaywallAuthor(JSONSerializable):
    given: str
    family: str
    sequence: str
    affiliation: Optional[List[str]] = field(default=None)


def get_unpaywall_work_by_doi(doi: str) -> UnpaywallWork:
    endpoint = f"https://api.unpaywall.org/v2/{doi}?email={EMAIL_ADDRESS}"
    response = get(endpoint)
    assert (
        response.status_code == 200
    ), f"unexpected status code {response.status_code}: {response.text}"
    return UnpaywallWork.from_dict(response.json())
