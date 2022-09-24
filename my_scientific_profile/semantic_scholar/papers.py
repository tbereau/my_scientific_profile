import logging
from typing import Optional

from my_scientific_profile.semantic_scholar.utils import (
    SemanticScholarPaper,
    fetch_info_by_id,
)

logger = logging.getLogger(__name__)


def get_paper_info(paper_id: str) -> Optional[SemanticScholarPaper]:
    fields = ["title", "authors", "abstract", "venue", "year", "isOpenAccess", "tldr"]
    info = fetch_info_by_id(paper_id, "paper", fields=fields)
    return SemanticScholarPaper.from_dict(info) if info else None
