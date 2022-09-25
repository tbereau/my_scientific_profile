import datetime as dt
import logging
from dataclasses import dataclass, field
from typing import List, Optional

import pandas as pd
from dataclass_wizard import JSONSerializable, json_field
from decouple import config as environ
from requests import get

import my_scientific_profile.utils  # noqa

__all__ = [
    "OrcidDate",
    "IntValue",
    "StrValue",
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
class OrcidDate(JSONSerializable):
    year: Optional["IntValue"] = json_field("year", default=None, repr=None)
    month: Optional["IntValue"] = json_field("month", default=None, repr=None)
    day: Optional["IntValue"] = json_field("day", default=None, repr=None)
    timestamp: Optional[int] = json_field("value", default=None, repr=None)
    datetime: dt.datetime = field(init=False)

    def __post_init__(self):
        assert self.timestamp or self.year.value
        if self.timestamp:
            object.__setattr__(
                self, "datetime", pd.to_datetime(self.timestamp, unit="ms")
            )
        else:
            date_in_str = f"{self.year.value}"
            date_in_str += f"".join(
                [f"-{str(x.value)}" for x in [self.month, self.day] if x]
            )
            object.__setattr__(self, "datetime", pd.to_datetime(date_in_str))


@dataclass(frozen=True)
class IntValue(JSONSerializable):
    value: Optional[int] = field(default=None)


@dataclass(frozen=True)
class StrValue(JSONSerializable):
    value: str


@dataclass(frozen=True)
class ExternalIdCollection(JSONSerializable):
    external_id: List["ExternalIds"]


@dataclass(frozen=True)
class ExternalIds(JSONSerializable):
    external_id_type: str
    external_id_value: str
    external_id_normalized: "ExternalId"
    external_id_normalized_error: str
    external_id_relationship: str
    external_id_url: Optional["ExternalId"] = field(default=None)


@dataclass(frozen=True)
class ExternalId(JSONSerializable):
    value: str
    transient: Optional[bool] = field(default=None)


@dataclass(frozen=True)
class Source(JSONSerializable):
    source_orcid: str
    source_name: ExternalId
    source_client_id: Optional["SourceClientId"] = field(default=None)
    assertion_origin_orcid: Optional[str] = field(default=None)
    assertion_origin_client_id: Optional[str] = field(default=None)
    assertion_origin_name: Optional[str] = field(default=None)


@dataclass(frozen=True)
class SourceClientId(JSONSerializable):
    uri: str
    path: str
    host: str


def get_orcid_request_endpoint_prefix() -> str:
    return f"https://pub.orcid.org/v3.0"


def get_orcid_request_endpoint_template(orcid_id: Optional[str] = MY_ORCID) -> str:
    prefix = get_orcid_request_endpoint_prefix()
    return f"{prefix}/{orcid_id}" if orcid_id else prefix


def get_orcid_request_headers() -> dict:
    return {
        "Content-Type": "application/orcid+json",
        "Authorization": f"Bearer {ORCID_CODE}",
    }


def get_orcid_query(
    query_type: str, orcid_id: Optional[str] = MY_ORCID, suffix: str = None
) -> dict:
    logger.info(f"fetching {query_type} {suffix}")
    endpoint = get_orcid_request_endpoint_template(orcid_id)
    endpoint += f"/{query_type}/{suffix}" if suffix else f"/{query_type}"
    logger.info(f"url {endpoint}")
    response = get(endpoint, headers=get_orcid_request_headers())
    assert (
        response.status_code == 200
    ), f"unexpected status code {response.status_code}: {response.text}"
    return response.json()
