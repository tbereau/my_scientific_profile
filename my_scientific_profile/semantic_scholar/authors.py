import logging

from pydantic import parse_obj_as

from my_scientific_profile.semantic_scholar.utils import (
    MY_SEMANTIC_ID,
    SemanticScholarAuthor,
    fetch_info_by_id,
)

logger = logging.getLogger(__name__)


def get_my_author_info(get_papers: bool = False) -> SemanticScholarAuthor:
    return get_author_info(MY_SEMANTIC_ID, get_papers=get_papers)


def get_author_info(author_id: str, get_papers: bool = False) -> SemanticScholarAuthor:
    fields = ["name", "aliases", "url", "hIndex", "citationCount"]
    if get_papers:
        fields.append("papers")
    info = fetch_info_by_id(author_id, "author", fields=fields)
    return parse_obj_as(SemanticScholarAuthor, info)
