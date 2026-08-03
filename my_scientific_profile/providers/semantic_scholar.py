import logging

from my_scientific_profile.papers.work_id import WorkId
from my_scientific_profile.providers.base import PartialRecord
from my_scientific_profile.semantic_scholar.papers import get_paper_info

__all__ = ["SemanticScholarProvider"]

logger = logging.getLogger(__name__)


class SemanticScholarProvider:
    """Semantic Scholar, the only source of a machine-written TL;DR."""

    name = "semantic_scholar"

    def supports(self, work_id: WorkId) -> bool:
        return work_id.doi is not None or work_id.scheme == "arxiv"

    def fetch(self, work_id: WorkId) -> PartialRecord | None:
        # Semantic Scholar resolves arXiv ids natively, which reaches papers it
        # has not linked to a DOI yet.
        lookup = (
            f"arXiv:{work_id.value}" if work_id.scheme == "arxiv" else work_id.doi
        )
        info = get_paper_info(lookup)
        if info is None:
            return None
        return PartialRecord(
            provider=self.name,
            title=info.title,
            abstract=info.abstract,
            tldr=info.tldr.text if info.tldr else None,
            citation_count=None,
        )
