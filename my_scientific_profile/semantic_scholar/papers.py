import logging
from functools import lru_cache

from pydantic import parse_obj_as

from my_scientific_profile.semantic_scholar.utils import (
    SemanticScholarPaper,
    fetch_info_by_id,
)

logger = logging.getLogger(__name__)


@lru_cache()
def get_paper_info(paper_id: str) -> SemanticScholarPaper | None:
    fields = ["title", "authors", "abstract", "venue", "year", "isOpenAccess", "tldr"]
    info = fetch_info_by_id(paper_id, "paper", fields=fields)
    return parse_obj_as(SemanticScholarPaper, info) if info else None
