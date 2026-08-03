import datetime as dt
import logging
from functools import lru_cache
from itertools import chain

from pydantic.dataclasses import dataclass

from my_scientific_profile.authors.authors import Author
from my_scientific_profile.config.config import (
    get_configured_work_keys,
    get_ignored_work_keys,
)
from my_scientific_profile.orcid.utils import get_my_orcid
from my_scientific_profile.orcid.works import get_work_id_to_put_code_map
from my_scientific_profile.papers.open_access import (
    OpenAccessPaperInfo,
    no_open_access_info,
)
from my_scientific_profile.papers.venue import JournalInfo, VenueInfo, VenueKind
from my_scientific_profile.papers.work_id import WorkId
from my_scientific_profile.providers.base import build_authors
from my_scientific_profile.providers.bibtex import render_bib_entry
from my_scientific_profile.providers.merge import ResolvedRecord, resolve_record
from my_scientific_profile.utils.singletons import PaperSingleton
from my_scientific_profile.utils.text import title_key, titles_match

__all__ = [
    "VenueKind",
    "VenueInfo",
    "JournalInfo",
    "Embedding",
    "Paper",
    "PaperResolutionError",
    "ResolutionIssue",
    "fetch_all_paper_infos",
    "fetch_paper_info",
    "fetch_paper_info_for_work_id",
    "fetch_all_paper_authors",
    "get_last_resolution_report",
]

logger = logging.getLogger(__name__)

SUPERSEDABLE_KINDS = (VenueKind.PREPRINT, VenueKind.REPOSITORY)

# Fields the website cites a source for, so provenance stays small enough to
# read while still covering everything shown as "from ...".
CITED_FIELDS = ("venue_name", "abstract", "tldr", "bib_entry", "open_access", "authors")


class PaperResolutionError(Exception):
    """No provider could supply enough metadata to build a Paper."""

    def __init__(self, key: str, stage: str, message: str) -> None:
        self.key = key
        self.stage = stage
        self.message = message
        super().__init__(f"{key}: [{stage}] {message}")


@dataclass(frozen=True)
class ResolutionIssue:
    key: str
    stage: str
    message: str


_LAST_REPORT: list[ResolutionIssue] = []


def get_last_resolution_report() -> list[ResolutionIssue]:
    """Works skipped, collapsed, or degraded during the last batch fetch.

    Only reflects resolutions actually performed: papers served from the
    singleton cache contribute nothing, since no provider was called for them.
    """
    return list(_LAST_REPORT)


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
    journal: VenueInfo
    publication_date: dt.datetime
    authors: list[Author]
    citation_count: int
    open_access: OpenAccessPaperInfo
    bib_entry: str | None = None
    abstract: str | None = None
    tldr: str | None = None
    year: int | None = None
    embedding: Embedding | None = None
    work_id: WorkId | None = None
    # Which provider supplied each of the fields the website attributes.
    provenance: dict[str, str] | None = None

    def __post_init__(self):
        object.__setattr__(self, "title", " ".join(self.title.split()))
        object.__setattr__(self, "year", self.publication_date.year)

    @classmethod
    def get_existing_paper(cls, doi: str) -> "Paper":
        return PaperSingleton._instances.get(doi)

    def source_of(self, field: str) -> str | None:
        return (self.provenance or {}).get(field)

    def to_yaml(self) -> str:
        authors = ""
        authors_list = [a.full_name for a in self.authors]
        for author in authors_list[:-1]:
            authors += author + ", "
        authors += authors_list[-1]
        return f"""- authors: {authors}
  title: "{self.title}"
  journal: "{self.journal.abbreviation or ""}"
  volume: {self.journal.volume or ""}
  year: {self.year}
  open_access_flag: {self.open_access.is_open_access}
  open_access_url: {self.open_access.landing_page_url or ""}
  open_access_pdf: {self.open_access.pdf_url or ""}
  doi: "{self.doi}"
"""


def _record(key: str, stage: str, message: str) -> None:
    _LAST_REPORT.append(ResolutionIssue(key=key, stage=stage, message=message))


def _same_work(title: str, candidates: dict[str, str]) -> str | None:
    """The DOI of the candidate whose title is close enough to be the same work."""
    for candidate_title, doi in candidates.items():
        if titles_match(candidate_title, title):
            return doi
    return None


def _drop_superseded_preprints(papers: list["Paper"]) -> list["Paper"]:
    """Collapse preprints onto the published work they became.

    An ORCID record lists a preprint alongside its journal version, and often
    one entry per preprint revision. They are the same paper, so listing each
    separately would count it two or three times. Papers must already be sorted
    newest first, so the surviving revision is the latest one.

    Two published works are never merged, however alike their titles.
    """
    published = {
        title_key(paper.title): paper.doi
        for paper in papers
        if paper.journal.kind not in SUPERSEDABLE_KINDS
    }
    kept: list[Paper] = []
    seen_preprints: dict[str, str] = {}
    for paper in papers:
        if paper.journal.kind not in SUPERSEDABLE_KINDS:
            kept.append(paper)
            continue
        if published_doi := _same_work(paper.title, published):
            _record(paper.doi, "superseded", f"published as {published_doi}")
            continue
        if previous := _same_work(paper.title, seen_preprints):
            _record(paper.doi, "superseded", f"earlier revision of {previous}")
            continue
        seen_preprints[title_key(paper.title)] = paper.doi
        kept.append(paper)
    return kept


def _venue_from(resolved: ResolvedRecord, work_id: WorkId) -> VenueInfo:
    record = resolved.record
    kind = record.venue_kind or (
        VenueKind.JOURNAL if record.venue_name else VenueKind.PREPRINT
    )
    if record.venue_name is None:
        logger.info(f"no venue name for {work_id.key} (kind {kind}); leaving it blank")
    return VenueInfo(
        url=record.url or f"https://doi.org/{work_id.doi}",
        kind=kind,
        name=record.venue_name,
        abbreviation=record.venue_abbreviation or record.venue_name,
        issue=record.issue,
        pages=record.pages,
        volume=record.volume,
    )


@lru_cache
def fetch_paper_info_for_work_id(work_id: WorkId, orcid_id: str = None) -> Paper:
    """Build a Paper from whatever the providers can tell us about a work.

    Raises PaperResolutionError when nothing can supply a title, a date or a
    DOI, so that an unresolvable work is reported rather than dropped.
    """
    doi = work_id.doi
    if doi is None:
        raise PaperResolutionError(
            work_id.key, "identity", "no DOI, and Paper is still keyed by DOI"
        )
    if existing_paper := Paper.get_existing_paper(doi):
        return existing_paper

    resolved = resolve_record(work_id, orcid_id)
    record = resolved.record
    for provider, message in resolved.outages:
        _record(work_id.key, provider, message)

    if not record.title:
        raise PaperResolutionError(
            work_id.key,
            "title",
            f"no provider has this work (tried {_tried(resolved)})",
        )
    if record.publication_date is None:
        raise PaperResolutionError(work_id.key, "publication_date", "no date available")

    paper = Paper(
        doi=doi,
        title=record.title,
        journal=_venue_from(resolved, work_id),
        publication_date=record.publication_date,
        authors=build_authors(record.authors),
        citation_count=record.citation_count or 0,
        open_access=record.open_access or no_open_access_info(),
        bib_entry=record.bib_entry,
        abstract=record.abstract,
        tldr=record.tldr,
        work_id=work_id,
        provenance={
            field: provider
            for field, provider in resolved.provenance.items()
            if field in CITED_FIELDS
        },
    )
    if not paper.authors:
        _record(work_id.key, "authors", "no provider listed any author")
    _finalise_bib_entry(paper)
    return paper


def _finalise_bib_entry(paper: Paper) -> None:
    """Render a BibTeX entry wherever content negotiation cannot do better.

    A conference paper is the interesting case: its DOI belongs to arXiv, so
    negotiation returns @misc citing a preprint. Once the venue is resolved we
    can state it properly, which is what a CV needs.
    """
    if paper.source_of("bib_entry") == "config":
        return
    if paper.bib_entry and paper.journal.kind != VenueKind.CONFERENCE:
        return
    paper.bib_entry = render_bib_entry(paper)
    paper.provenance = {**(paper.provenance or {}), "bib_entry": "rendered"}


def _tried(resolved: ResolvedRecord) -> str:
    outages = {provider for provider, _ in resolved.outages}
    return ", ".join(sorted(outages)) if outages else "every provider"


@lru_cache
def fetch_paper_info(doi: str, orcid_id: str = None) -> Paper:
    """Build a Paper for one DOI, arXiv DOIs included."""
    return fetch_paper_info_for_work_id(WorkId.from_doi(doi), orcid_id)


def _all_work_ids(orcid_id: str = None) -> list[WorkId]:
    """Everything to list: the ORCID record, plus works named in the config.

    ORCID is the authority on what counts as one's own work, but it cannot
    describe what no indexer has yet, so the config may name a work outright.
    """
    ignored = get_ignored_work_keys()

    def is_ignored(work_id: WorkId) -> bool:
        return work_id.key in ignored or (work_id.doi or "") in ignored

    work_ids = [
        work_id
        for work_id in get_work_id_to_put_code_map(orcid_id)
        if not is_ignored(work_id)
    ]
    known = set(work_ids)
    for key in get_configured_work_keys():
        work_id = WorkId.parse(key)
        if work_id not in known and not is_ignored(work_id):
            logger.info(f"listing {work_id.key} on the strength of the config alone")
            work_ids.append(work_id)
            known.add(work_id)
    return work_ids


def fetch_all_paper_infos(orcid_id: str = None) -> list[Paper]:
    work_ids = _all_work_ids(orcid_id)
    if not orcid_id:
        orcid_id = get_my_orcid()
    _LAST_REPORT.clear()
    papers = []
    for work_id in work_ids:
        try:
            papers.append(fetch_paper_info_for_work_id(work_id, orcid_id))
        except PaperResolutionError as error:
            logger.warning(f"skipping {error}")
            _record(error.key, error.stage, error.message)
        except Exception as error:  # one malformed record must not sink the batch
            logger.warning(f"skipping {work_id.key}: {error!r}", exc_info=True)
            _record(work_id.key, "unexpected", f"{type(error).__name__}: {error}")
    papers = sorted(
        papers,
        key=lambda x: (
            x.publication_date.replace(tzinfo=None)
            if x.publication_date
            else dt.datetime.min
        ),
        reverse=True,
    )
    papers = _drop_superseded_preprints(papers)
    _log_resolution_summary(len(papers), len(work_ids))
    return papers


def _log_resolution_summary(listed: int, total: int) -> None:
    if not _LAST_REPORT:
        logger.info(f"listing all {total} works")
        return
    superseded = [i for i in _LAST_REPORT if i.stage == "superseded"]
    other = [i for i in _LAST_REPORT if i.stage != "superseded"]
    detail = "\n".join(
        f"  {issue.key}: [{issue.stage}] {issue.message}" for issue in _LAST_REPORT
    )
    logger.warning(
        f"listing {listed}/{total} works "
        f"({len(superseded)} superseded, {len(other)} unresolved or degraded):\n"
        f"{detail}"
    )


def fetch_all_paper_authors() -> list[Author]:
    return list(
        set(chain.from_iterable([paper.authors for paper in fetch_all_paper_infos()]))
    )
