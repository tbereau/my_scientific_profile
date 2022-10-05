import json
from typing import Any

from lunr import lunr
from pydantic.json import pydantic_encoder

from my_scientific_profile.database.papers import load_all_papers_from_s3
from my_scientific_profile.web_app.extensions import S3_BUCKET, s3_client

__all__ = ["get_all_paper_documents", "get_search_index"]


def get_search_index() -> Any:
    return lunr(
        ref="doi",
        fields=[
            "title",
            "abstract",
            dict(field_name="journal_name", extractor=lambda d: d["journal"]["name"]),
            dict(
                field_name="journal_abbreviation",
                extractor=lambda d: d["journal"]["abbreviation"],
            ),
            dict(
                field_name="authors_given",
                extractor=lambda d: " ".join([x["given"] for x in d["authors"][:]]),
            ),
            dict(
                field_name="authors_family",
                extractor=lambda d: " ".join([x["family"] for x in d["authors"][:]]),
            ),
        ],
        documents=get_all_paper_documents(),
    )


def get_all_paper_documents() -> list[dict]:
    papers = load_all_papers_from_s3(s3_client, S3_BUCKET)
    return [json.loads(json.dumps(paper, default=pydantic_encoder)) for paper in papers]
