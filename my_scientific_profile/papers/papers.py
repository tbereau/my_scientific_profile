import datetime as dt
import logging
from functools import lru_cache
from itertools import chain

from pydantic.dataclasses import dataclass

from my_scientific_profile.authors.authors import (
    Author,
    get_author_from_orcid_or_crossref,
)
from my_scientific_profile.config.config import get_abstract_from_config
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
from my_scientific_profile.utils.singletons import PaperSingleton

__all__ = [
    "JournalInfo",
    "Embedding",
    "Paper",
    "fetch_all_paper_infos",
    "fetch_paper_info",
    "fetch_all_paper_authors",
]

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class JournalInfo:
    name: str
    url: str
    issue: str | None = None
    abbreviation: str | None = None
    pages: str | None = None
    volume: int | None = None


@dataclass
class Embedding:
    x: float
    y: float
    topic_number: int
    topic_name: str


@dataclass
class Paper(object, metaclass=PaperSingleton):
    doi: str
    title: str
    journal: JournalInfo
    publication_date: dt.datetime
    authors: list[Author]
    citation_count: int
    open_access: OpenAccessPaperInfo
    bib_entry: str
    abstract: str | None = None
    tldr: str | None = None
    year: int | None = None
    embedding: Embedding | None = None

    def __post_init__(self):
        object.__setattr__(self, "title", " ".join(self.title.split()))
        object.__setattr__(self, "year", self.publication_date.year)

    @classmethod
    def get_existing_paper(cls, doi: str) -> "Paper":
        return PaperSingleton._instances.get(doi)

    def to_yaml(self) -> str:
        authors = ""
        authors_list = [a.full_name for a in self.authors]
        for author in authors_list[:-1]:
            authors += author + ", "
        authors += authors_list[-1]
        return f"""- authors: {authors}
  title: "{self.title}"
  journal: "{self.journal.abbreviation}"
  volume: {self.journal.volume or ""}
  year: {self.year}
  open_access_flag: {self.open_access.is_open_access}
  open_access_url: {self.open_access.landing_page_url or ""}
  open_access_pdf: {self.open_access.pdf_url or ""}
  doi: "{self.doi}"
"""


@lru_cache
def fetch_paper_info(doi: str) -> Paper | None:
    if existing_paper := Paper.get_existing_paper(doi):
        return existing_paper
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
        abbreviation=crossref_info.message.short_title,
        url=url,
    )
    abstract = (
        semantic_info.abstract
        if semantic_info
        else crossref_info.message.abstract or get_abstract_from_config(doi)
    )
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
    papers = []
    for doi in dois:
        try:
            papers.append(fetch_paper_info(doi))
        except AssertionError:
            logger.info(f"WARNING! Cannot parse doi {doi}")
    return papers


def fetch_all_paper_authors() -> list[Author]:
    return list(
        set(chain.from_iterable([paper.authors for paper in fetch_all_paper_infos()]))
    )
