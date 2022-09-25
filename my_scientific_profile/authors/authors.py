import logging
from dataclasses import dataclass, field
from typing import Optional

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
class Author:
    given: str
    family: str
    affiliation: "Affiliation"
    orcid: Optional[str] = field(default=None)
    email: Optional[str] = field(default=None)
    picture_path: Optional[str] = field(default=None)
    twitter: Optional[str] = field(default=None)
    google_scholar: Optional[str] = field(default=None)
    research_gate: Optional[str] = field(default=None)

    @property
    def full_name(self) -> str:
        return " ".join([self.given, self.family])


@dataclass(frozen=True)
class Affiliation:
    name: Optional[str] = field(default=None)
    city: Optional[str] = field(default=None)
    country: Optional[str] = field(default=None)


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
        orcid_author.given,
        orcid_author.family,
        affiliation=get_affiliation_from_orcid(orcid_author.last_organization),
        orcid=orcid_author.orcid,
        email=orcid_author.email[0] if orcid_author.email else None,
    )


def search_crossref_author_in_orcid(author_info: CrossrefAuthor) -> Optional[Author]:
    if author_info.orcid:
        orcid_search = search_for_author_by_orcid_id(author_info.orcid)
    else:
        orcid_search = search_for_author_by_name(author_info.given, author_info.family)
    if len(orcid_search) != 1:
        logger.info(
            f"ORCID search results returned {len(orcid_search)} results\n{orcid_search}"
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
