import datetime as dt
from dataclasses import dataclass
from typing import List, Optional

from my_scientific_profile.authors.authors import (
    Author,
    get_author_from_orcid_or_crossref,
)
from my_scientific_profile.crossref.works import get_crossref_work_by_doi
from my_scientific_profile.doi2bib.doi2bib import fetch_bib
from my_scientific_profile.papers.open_access import (
    OpenAccessPaperInfo,
    get_open_access_paper_info,
)
from my_scientific_profile.semantic_scholar.papers import (
    get_paper_info as get_semantic_scholar_paper_info,
)


@dataclass
class Paper:
    doi: str
    title: str
    abstract: str
    journal: "JournalInfo"
    publication_date: dt.datetime
    authors: List[Author]
    citation_count: int
    open_access: OpenAccessPaperInfo
    bib_entry: str
    tldr: Optional[str]

    def __post_init__(self):
        object.__setattr__(self, "title", " ".join(self.title.split()))

    @property
    def year(self) -> int:
        return self.publication_date.year


@dataclass(frozen=True)
class JournalInfo:
    name: str
    abbreviation: str
    url: str


def fetch_paper_info(doi: str) -> Paper:
    crossref_info = get_crossref_work_by_doi(doi)
    semantic_info = get_semantic_scholar_paper_info(doi)
    bib_info = fetch_bib(doi)
    journal_info = JournalInfo(
        crossref_info.message.container_title[0],
        crossref_info.message.short_container_title[0],
        crossref_info.message.url,
    )
    abstract = (
        semantic_info.abstract if semantic_info else crossref_info.message.abstract
    )
    authors = [
        get_author_from_orcid_or_crossref(author)
        for author in crossref_info.message.author
    ]
    open_access_info = get_open_access_paper_info(doi)
    return Paper(
        doi,
        crossref_info.message.title[0],
        abstract,
        journal_info,
        crossref_info.message.created.date_time,
        authors,
        crossref_info.message.is_referenced_by_count,
        open_access_info,
        bib_entry=bib_info,
        tldr=semantic_info.tldr.text if semantic_info and semantic_info.tldr else None,
    )
