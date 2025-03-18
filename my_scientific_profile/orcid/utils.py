import datetime as dt
import logging
from typing import Optional

import pandas as pd
from decouple import config as environ
from humps import dekebabize
from pydantic import Field, HttpUrl
from pydantic.dataclasses import dataclass
from requests import get

import my_scientific_profile.utils  # noqa
from my_scientific_profile.config.required_environment_variables import assert_all_environment_variables
from my_scientific_profile.config.config import get_my_orcid

__all__ = [
    "OrcidDate",
    "IntValue",
    "StrValue",
    "UrlValue",
    "ExternalId",
    "ExternalIds",
    "ExternalIdCollection",
    "Source",
    "SourceClientId",
    "get_orcid_request_headers",
    "get_orcid_query",
    "get_orcid_request_endpoint_template",
]

logger = logging.getLogger(__name__)

ORCID_CODE = environ("ORCID_CODE")
MY_ORCID = get_my_orcid()

assert_all_environment_variables("orcid")


@dataclass(frozen=True)
class IntValue:
    value: int | None = None


@dataclass(frozen=True)
class OrcidDate:
    year: IntValue | None = Field(alias="year", default=None, repr=False)
    month: IntValue | None = Field(alias="month", default=None, repr=False)
    day: IntValue | None = Field(alias="day", default=None, repr=False)
    timestamp: int | None = Field(alias="value", default=None, repr=False)

    @property
    def datetime(self) -> dt.datetime:
        assert self.timestamp or self.year.value
        if self.timestamp:
            return pd.to_datetime(self.timestamp, unit="ms")
        else:
            date_in_str = f"{self.year.value}"
            date_in_str += "".join(
                [f"-{str(x.value)}" for x in [self.month, self.day] if x]
            )
            return pd.to_datetime(date_in_str)


@dataclass(frozen=True)
class StrValue:
    value: str


@dataclass(frozen=True)
class UrlValue:
    value: HttpUrl


@dataclass(frozen=True)
class ExternalId:
    value: str
    transient: bool = None


@dataclass(frozen=True)
class ExternalIds:
    external_id_type: str
    external_id_value: str
    external_id_normalized: ExternalId
    external_id_normalized_error: Optional[str] = None
    external_id_relationship: Optional[str] = None
    external_id_url: Optional[ExternalId] = None


@dataclass(frozen=True)
class ExternalIdCollection:
    external_id: list[ExternalIds]


@dataclass(frozen=True)
class SourceClientId:
    uri: str
    path: str
    host: str


@dataclass(frozen=True)
class Origin:
    uri: HttpUrl
    path: str
    host: str


@dataclass(frozen=True)
class Source:
    source_name: ExternalId
    source_orcid: Optional[Origin] = None
    source_client_id: Optional[SourceClientId] = None
    assertion_origin_orcid: Optional[Origin] = None
    assertion_origin_client_id: Optional[Origin] = None
    assertion_origin_name: Optional[StrValue] = None


def get_orcid_request_endpoint_prefix() -> str:
    return "https://pub.orcid.org/v3.0"


def get_orcid_request_endpoint_template(orcid_id: str | None = MY_ORCID) -> str:
    prefix = get_orcid_request_endpoint_prefix()
    return f"{prefix}/{orcid_id}" if orcid_id else prefix


def get_orcid_request_headers() -> dict:
    return {
        "Content-Type": "application/orcid+json",
        "Authorization": f"Bearer {ORCID_CODE}",
    }


def get_orcid_query(
    query_type: str,
    orcid_id: str | None = MY_ORCID,
    suffix: str = None,
) -> dict:
    logger.info(f"fetching {query_type} {suffix} with ORCID {orcid_id}")
    endpoint = get_orcid_request_endpoint_template(orcid_id)
    endpoint += f"/{query_type}/{suffix}" if suffix else f"/{query_type}"
    logger.info(f"url {endpoint}")
    response = get(endpoint, headers=get_orcid_request_headers())
    assert (
        response.status_code == 200
    ), f"unexpected status code {response.status_code}: {response.text}"
    return dekebabize(response.json())
