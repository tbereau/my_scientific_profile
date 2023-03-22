import logging
import uuid

from pydantic.dataclasses import dataclass
from unidecode import unidecode

from my_scientific_profile.crossref.utils import CrossrefAuthor
from my_scientific_profile.orcid.authors import (
    OrcidAuthor,
    search_for_author_by_name,
    search_for_author_by_orcid_id,
)
from my_scientific_profile.orcid.employments import OrcidOrganization
from my_scientific_profile.utils.singletons import AuthorSingleton

__all__ = [
    "Author",
    "get_author_from_crossref",
    "get_author_from_orcid_or_crossref",
    "search_crossref_author_in_orcid",
    "search_author_from_config_info",
]

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Affiliation:
    name: str = None
    city: str = None
    country: str = None

    @property
    def is_empty(self) -> bool:
        return all(
            object.__getattribute__(self, key) is None
            for key in ["name", "city", "country"]
        )


@dataclass(frozen=True)
class Author(object, metaclass=AuthorSingleton):
    given: str
    family: str
    affiliation: Affiliation = None
    orcid: str = None
    email: str = None
    full_name: str = None
    uuid: str = None

    def __post_init__(self):
        object.__setattr__(self, "given", self.given.title())
        object.__setattr__(self, "family", self.family.title())
        object.__setattr__(self, "full_name", " ".join([self.given, self.family]))
        object.__setattr__(self, "uuid", str(uuid.uuid1()))

    def __eq__(self, other: "Author") -> bool:
        return self.family == other.family and self.given[0] == other.given[0]

    def combine_with_other_author(self, other: "Author") -> "Author":
        assert self.given[0] == other.given[0], f"mismatch {self} vs {other}"
        assert self.family == other.family, f"mismatch {self} vs {other}"
        given = max(self.given, other.given, key=lambda x: len(x))
        family = self.family
        affiliation = (
            self.affiliation if other.affiliation.is_empty else other.affiliation
        )
        logger.debug(
            f"affiliation {self.affiliation} {other.affiliation} {affiliation}"
        )
        params = {
            "given": given,
            "family": family,
            "full_name": " ".join([given, family]),
            "affiliation": affiliation,
            "orcid": self.orcid or other.orcid,
            "email": self.email or other.email,
            "uuid": min(self.uuid, other.uuid),
        }
        for instance in [self, other]:
            for key, value in params.items():
                object.__setattr__(instance, key, value)

    @classmethod
    def get_existing_crossref_author(cls, author: CrossrefAuthor) -> "Author" or None:
        matching_authors = (
            a
            for a in AuthorSingleton._instances
            if a.family == author.family and a.given[0] == author.given[0]
        )
        return next(matching_authors, None)

    @classmethod
    def get_existing_author(cls, author_info: dict) -> "Author" or None:
        matching_authors = (
            a
            for a in AuthorSingleton._instances
            if (
                author_info.get("orcid")
                and a.orcid == author_info.get("orcid")  # noqa
                or (  # noqa
                    author_info.get("family") == a.family  # noqa
                    and author_info.get("given")[0] == a.given[0]  # noqa
                )
            )
        )
        return next(matching_authors, None)

    @property
    def lower_case_snake_name(self) -> str:
        return unidecode(
            "_".join([self.given.lower(), self.family.lower()])
            .replace(".", "")
            .replace(" ", "_")
        )


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
    logger.debug(f"convert {orcid_author}")
    logger.debug(f"convert {orcid_author.last_organization}")
    return Author(
        orcid_author.given_names,
        orcid_author.family_names,
        affiliation=get_affiliation_from_orcid(orcid_author.last_organization),
        orcid=orcid_author.orcid_id,
        email=orcid_author.email[0] if orcid_author.email else None,
    )


def search_crossref_author_in_orcid(author_info: CrossrefAuthor) -> Author | None:
    if author := Author.get_existing_crossref_author(author_info):
        return author
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


def search_author_from_config_info(author_info: dict) -> Author:
    if author := Author.get_existing_author(author_info):
        return author
    if author_info.get("orcid"):
        orcid_search = search_for_author_by_orcid_id(author_info.get("orcid"))
    else:
        orcid_search = search_for_author_by_name(
            author_info.get("given"), author_info.get("family")
        )
    if len(orcid_search) != 1:
        logger.info(
            f"ORCID search results returned {len(orcid_search)} "
            f"results\n{orcid_search[:3]} {'...' if len(orcid_search) > 3 else ''}"
        )
        return None
    return convert_orcid_author_to_author(orcid_search[0])
