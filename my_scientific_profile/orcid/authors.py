import logging
import re
from dataclasses import dataclass, field
from functools import lru_cache
from typing import List, Optional

from dataclass_wizard import JSONSerializable, json_field

from my_scientific_profile.orcid.employments import (
    OrcidEmployment,
    OrcidOrganization,
    fetch_employment_for_orcid_id,
    get_last_organization,
)
from my_scientific_profile.orcid.utils import get_orcid_query

logger = logging.getLogger(__name__)


@dataclass
class OrcidAuthor(JSONSerializable):
    given: str = json_field(["given-names"])
    family: str = json_field(["family-names"])
    orcid: str = json_field(["orcid-id"])
    credit_name: Optional[str] = json_field(["credit-name"])
    other_name: List[str] = field(default_factory=list)
    email: List[str] = field(default_factory=list)

    _employment: Optional[OrcidEmployment] = field(default=None)
    _organization: Optional[OrcidOrganization] = field(default=None)

    @property
    def employment(self) -> OrcidEmployment:
        if self._employment is None:
            self._employment = fetch_employment_for_orcid_id(self.orcid)
        return self._employment

    @property
    def last_organization(self) -> Optional[OrcidOrganization]:
        return get_last_organization(self.employment)


@lru_cache()
def search_for_author_by_name(given_name: str, family_name: str) -> List[OrcidAuthor]:
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
        [OrcidAuthor.from_dict(response) for response in responses["expanded-result"]]
        if num_response > 0
        else []
    )


@lru_cache()
def search_for_author_by_orcid_id(orcid_id: str) -> List[OrcidAuthor]:
    responses = get_orcid_query(
        "expanded-search", orcid_id=None, suffix=f"?q=orcid:{orcid_id}"
    )
    num_response = int(responses["num-found"])
    logger.info(f"Entries received: {num_response}")
    return (
        [OrcidAuthor.from_dict(response) for response in responses["expanded-result"]]
        if num_response == 1
        else []
    )
