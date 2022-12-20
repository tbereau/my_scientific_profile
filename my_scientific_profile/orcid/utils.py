import datetime as dt
import logging

import pandas as pd
from decouple import config as environ
from humps import decamelize
from pydantic import Field, HttpUrl
from pydantic.dataclasses import dataclass
from requests import get

import my_scientific_profile.utils  # noqa

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
MY_ORCID = "0000-0001-9945-1271"


@dataclass(frozen=True)
class IntValue:
    value: int = None


@dataclass(frozen=True)
class OrcidDate:
    year: IntValue = Field(alias="year", default=None, repr=False)
    month: IntValue = Field(alias="month", default=None, repr=False)
    day: IntValue = Field(alias="day", default=None, repr=False)
    timestamp: int = Field(alias="value", default=None, repr=False)

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
    external_id_normalized_error: str = None
    external_id_relationship: str = None
    external_id_url: ExternalId = None


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
    source_orcid: Origin = None
    source_client_id: SourceClientId = None
    assertion_origin_orcid: Origin = None
    assertion_origin_client_id: Origin = None
    assertion_origin_name: StrValue = None


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
    query_type: str, orcid_id: str | None = MY_ORCID, suffix: str = None
) -> dict:
    logger.info(f"fetching {query_type} {suffix}")
    endpoint = get_orcid_request_endpoint_template(orcid_id)
    endpoint += f"/{query_type}/{suffix}" if suffix else f"/{query_type}"
    logger.info(f"url {endpoint}")
    response = get(endpoint, headers=get_orcid_request_headers())
    assert (
        response.status_code == 200
    ), f"unexpected status code {response.status_code}: {response.text}"
    return decamelize(response.json())
