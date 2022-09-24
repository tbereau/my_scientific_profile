import datetime as dt
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd
from dataclass_wizard import JSONSerializable, json_field
from decouple import config as environ

import my_scientific_profile.utils  # noqa

__all__ = [
    "OrcidDate",
    "IntValue",
    "StrValue",
    "get_orcid_request_headers",
    "get_orcid_request_endpoint_template",
]

ORCID_CODE = environ("ORCID_CODE")
MY_ORCID = "0000-0001-9945-1271"


@dataclass(frozen=True)
class OrcidDate(JSONSerializable):
    timestamp: int = json_field("value", repr=None)
    datetime: dt.datetime = field(init=False)

    def __post_init__(self):
        object.__setattr__(self, "datetime", pd.to_datetime(self.timestamp, unit="ms"))


@dataclass(frozen=True)
class IntValue(JSONSerializable):
    value: Optional[int] = field(default=None)


@dataclass(frozen=True)
class StrValue(JSONSerializable):
    value: str


def get_orcid_request_endpoint_template() -> str:
    return f"https://pub.orcid.org/v3.0/{MY_ORCID}"


def get_orcid_request_headers() -> dict:
    return {
        "Content-Type": "application/orcid+json",
        "Authorization": f"Bearer {ORCID_CODE}",
    }
