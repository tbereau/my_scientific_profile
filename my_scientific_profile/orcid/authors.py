import logging
import re
from functools import lru_cache

from humps import dekebabize
from pydantic import parse_obj_as
from pydantic.dataclasses import dataclass

from my_scientific_profile.orcid.employments import (
    OrcidEmployment,
    OrcidOrganization,
    fetch_employment_for_orcid_id,
    get_last_organization,
)
from my_scientific_profile.orcid.utils import get_orcid_query

logger = logging.getLogger(__name__)


@dataclass
class OrcidAuthor:
    given_names: str
    family_names: str
    orcid_id: str = None
    credit_name: str = None
    other_name: list[str] = None
    email: list[str] = None

    @property
    def employment(self) -> OrcidEmployment:
        return fetch_employment_for_orcid_id(self.orcid_id)

    @property
    def last_organization(self) -> OrcidOrganization | None:
        return get_last_organization(self.employment)


@lru_cache()
def search_for_author_by_name(given_name: str, family_name: str) -> list[OrcidAuthor]:
    responses = get_orcid_query(
        "expanded-search",
        orcid_id=None,
        suffix=(
            f"?q=given-names:{re.escape(given_name)}"
            f"+AND+family-name:{re.escape(family_name)}"
        ),
    )
    num_response = int(responses["num-found"])
    logger.info(f"Entries received: {num_response}")
    return (
        [
            parse_obj_as(OrcidAuthor, dekebabize(response))
            for response in responses["expanded-result"]
        ]
        if num_response > 0
        else []
    )


@lru_cache()
def search_for_author_by_orcid_id(orcid_id: str) -> list[OrcidAuthor]:
    responses = get_orcid_query(
        "expanded-search", orcid_id=None, suffix=f"?q=orcid:{orcid_id}"
    )
    num_response = int(responses["num-found"])
    logger.info(f"Entries received: {num_response}")
    return (
        [
            parse_obj_as(OrcidAuthor, dekebabize(response))
            for response in responses["expanded-result"]
        ]
        if num_response == 1
        else []
    )
