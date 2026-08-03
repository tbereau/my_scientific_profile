import logging
from yaml import YAMLObject

from my_scientific_profile import CONFIG

__all__ = [
    "get_my_orcid",
    "get_author_configs",
    "get_paper_configs",
    "get_abstract_from_config",
    "find_author_in_config",
    "find_paper_config",
    "get_configured_work_keys",
    "get_ignored_work_keys",
    "get_authors_with_categories",
]

logger = logging.getLogger(__name__)


def get_my_orcid() -> str:
    return CONFIG["my-orcid"].get(str)


def get_s3_bucket() -> str:
    return CONFIG["s3-bucket"].get(str)


def get_email_address() -> str:
    return CONFIG["email-address"].get(str)


def get_author_configs() -> list[dict]:
    return [dict(e) for e in CONFIG["authors"].get()]


def get_paper_configs() -> list[dict]:
    try:
        return [dict(e) for e in CONFIG["papers"].get()]
    except Exception:  # an absent or empty papers section is not a failure
        logger.info("no paper overrides configured")
        return []


def get_ignored_work_keys() -> set[str]:
    """Works marked `ignore: true`, which are neither listed nor reported.

    A publication list is not everything with one's name on it: conference
    abstracts, translations and theses are usually deliberately left out. Say
    so once and the drift report stops raising them, so it stays worth reading.
    """
    keys = set()
    for entry in get_paper_configs():
        if not entry.get("ignore"):
            continue
        for field in ("id", "doi"):
            if entry.get(field):
                keys.add(str(entry[field]))
    return keys


def get_configured_work_keys() -> list[str]:
    """Work identifiers the config asks for by `id`, to be listed alongside ORCID.

    ORCID stays the record of what counts as one's own work, but it lags: a
    paper accepted at a conference whose proceedings are not out yet may be
    listed nowhere an API can see. An entry written with `id` says to list that
    work; the older `doi` spelling only overrides fields on a work ORCID
    already knows, so no existing entry can resurrect something removed there.
    """
    return [
        str(entry["id"])
        for entry in get_paper_configs()
        if entry.get("id") and not entry.get("ignore")
    ]


def find_paper_config(doi: str | None = None, work_key: str | None = None) -> dict:
    """The override entry for a work, matched on `id` or on `doi`.

    `id` is a `scheme:value` work identifier, which is how a work with no DOI
    of its own gets named; `doi` is the older spelling and still works.
    """
    for entry in get_paper_configs():
        entry_id = entry.get("id")
        if entry_id and work_key and str(entry_id) == work_key:
            return entry
        if doi and entry.get("doi") == doi:
            return entry
        # An `id` given as a bare DOI should match the DOI too.
        if entry_id and doi and str(entry_id) == doi:
            return entry
    return {}


def find_author_in_config(
    given: str, family: str, orcid: str = None
) -> YAMLObject | dict:
    author_configs = get_author_configs()
    for author in author_configs:
        if orcid is not None and author.get("orcid"):
            if author["orcid"] == orcid:
                return author
        else:
            if author["family"] == family and author["given"] == given:
                return author
    return {}


def get_abstract_from_config(doi: str) -> str:
    return find_paper_config(doi=doi).get("abstract") or ""


def get_authors_with_categories() -> list[dict]:
    authors = []
    for author in get_author_configs():
        if author.get("categories"):
            authors.append(author)
    return authors
