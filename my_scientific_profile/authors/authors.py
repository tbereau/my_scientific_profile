import logging
import uuid

from pydantic.dataclasses import dataclass

from my_scientific_profile.crossref.utils import CrossrefAuthor
from my_scientific_profile.orcid.authors import (
    OrcidAuthor,
    search_for_author_by_name,
    search_for_author_by_orcid_id,
)
from my_scientific_profile.orcid.employments import OrcidOrganization

__all__ = ["Author", "get_author_from_crossref", "get_author_from_orcid_or_crossref"]

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Affiliation:
    name: str = None
    city: str = None
    country: str = None


@dataclass(frozen=True)
class Author:
    given: str
    family: str
    affiliation: Affiliation
    orcid: str = None
    email: str = None
    full_name: str = None
    uuid: str = None

    def __post_init__(self):
        object.__setattr__(self, "given", self.given.title())
        object.__setattr__(self, "family", self.family.title())
        object.__setattr__(self, "full_name", " ".join([self.given, self.family]))
        object.__setattr__(self, "uuid", str(uuid.uuid1()))


def get_author_from_crossref(author_info: CrossrefAuthor) -> Author:
    affiliation_name = (
        author_info.affiliation[0].name if author_info.affiliation else None
    )
    return Author(
        author_info.given,
        author_info.family,
        affiliation=Affiliation(affiliation_name),
        orcid=author_info.orcid,
    )


def convert_orcid_author_to_author(orcid_author: OrcidAuthor) -> Author:
    return Author(
        orcid_author.given_names,
        orcid_author.family_names,
        affiliation=get_affiliation_from_orcid(orcid_author.last_organization),
        orcid=orcid_author.orcid_id,
        email=orcid_author.email[0] if orcid_author.email else None,
    )


def search_crossref_author_in_orcid(author_info: CrossrefAuthor) -> Author | None:
    if author_info.orcid:
        orcid_search = search_for_author_by_orcid_id(author_info.orcid)
    else:
        orcid_search = search_for_author_by_name(author_info.given, author_info.family)
    if len(orcid_search) != 1:
        logger.info(
            f"ORCID search results returned {len(orcid_search)} "
            f"results\n{orcid_search[:3]} {'...' if len(orcid_search) > 3 else ''}"
        )
        return None
    return convert_orcid_author_to_author(orcid_search[0])


def get_author_from_orcid_or_crossref(author_info: CrossrefAuthor) -> Author:
    orcid_author = search_crossref_author_in_orcid(author_info)
    return orcid_author or get_author_from_crossref(author_info)


def get_affiliation_from_orcid(orcid_organization: OrcidOrganization) -> Affiliation:
    return (
        Affiliation(
            orcid_organization.name,
            orcid_organization.address.city,
            orcid_organization.address.country,
        )
        if orcid_organization
        else Affiliation()
    )
