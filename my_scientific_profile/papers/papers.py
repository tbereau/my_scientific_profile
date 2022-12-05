import datetime as dt
from functools import lru_cache
from itertools import chain

from pydantic.dataclasses import dataclass

from my_scientific_profile.authors.authors import (
    Author,
    get_author_from_orcid_or_crossref,
)
from my_scientific_profile.crossref.works import get_crossref_work_by_doi
from my_scientific_profile.doi2bib.doi2bib import fetch_bib
from my_scientific_profile.orcid.detailed_work import get_detailed_work
from my_scientific_profile.orcid.works import get_doi_to_put_code_map
from my_scientific_profile.papers.open_access import (
    OpenAccessPaperInfo,
    get_open_access_paper_info,
)
from my_scientific_profile.semantic_scholar.papers import (
    get_paper_info as get_semantic_scholar_paper_info,
)

__all__ = [
    "JournalInfo",
    "Paper",
    "fetch_all_paper_infos",
    "fetch_paper_info",
    "fetch_all_paper_authors",
]


@dataclass(frozen=True)
class JournalInfo:
    name: str
    volume: int
    url: str
    issue: str = None
    abbreviation: str = None
    pages: str = None


@dataclass
class Paper:
    doi: str
    title: str
    journal: JournalInfo
    publication_date: dt.datetime
    authors: list[Author]
    citation_count: int
    open_access: OpenAccessPaperInfo
    bib_entry: str
    abstract: str = None
    tldr: str = None
    year: int = None

    def __post_init__(self):
        object.__setattr__(self, "title", " ".join(self.title.split()))
        object.__setattr__(self, "year", self.publication_date.year)


@lru_cache
def fetch_paper_info(doi: str) -> Paper:
    crossref_info = get_crossref_work_by_doi(doi)
    semantic_info = get_semantic_scholar_paper_info(doi)
    orcid_info = get_detailed_work(get_doi_to_put_code_map()[doi])
    bib_info = fetch_bib(doi)
    orcid_url = orcid_info.url.value if orcid_info.url else None
    url = crossref_info.message.url or orcid_url or f"https://doi.org/{doi}"
    journal_info = JournalInfo(
        name=crossref_info.message.container_title[0] or orcid_info.journal_title,
        issue=crossref_info.message.issue,
        volume=crossref_info.message.volume,
        pages=crossref_info.message.page,
        abbreviation=crossref_info.message.short_container_title[0],
        url=url,
    )
    abstract = (
        semantic_info.abstract if semantic_info else None
    ) or crossref_info.message.abstract
    authors = [
        get_author_from_orcid_or_crossref(author)
        for author in crossref_info.message.author
    ]
    open_access_info = get_open_access_paper_info(doi)
    return Paper(
        doi=doi,
        title=crossref_info.message.title[0],
        journal=journal_info,
        publication_date=crossref_info.message.created.date_time,
        authors=authors,
        citation_count=crossref_info.message.is_referenced_by_count,
        open_access=open_access_info,
        bib_entry=bib_info,
        abstract=abstract,
        tldr=semantic_info.tldr.text if semantic_info and semantic_info.tldr else None,
    )


def fetch_all_paper_infos() -> list[Paper]:
    dois = get_doi_to_put_code_map().keys()
    return [fetch_paper_info(doi) for doi in dois]


def fetch_all_paper_authors() -> list[Author]:
    return list(
        set(chain.from_iterable([paper.authors for paper in fetch_all_paper_infos()]))
    )
