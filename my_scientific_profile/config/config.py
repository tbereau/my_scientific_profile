import logging
import os

import yaml
from yaml import YAMLObject

from my_scientific_profile.utils.utils import ROOT_DIR

__all__ = [
    "CONFIG_PATH",
    "get_author_configs",
    "find_author_in_config",
    "get_authors_with_categories",
]

logger = logging.getLogger(__name__)

CONFIG_PATH = os.path.join(ROOT_DIR, "config")


def get_author_configs() -> list:
    return get_config("authors.yaml")


def get_paper_configs() -> list:
    return get_config("papers.yaml")


def get_config(yaml_file: str) -> list:
    with open(os.path.join(CONFIG_PATH, yaml_file), "r") as stream:
        try:
            config = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            logger.error(f"error in configuration file {yaml_file}")
            raise exc
    return config


def find_author_in_config(
    given: str, family: str, orcid: str = None
) -> YAMLObject | dict:
    author_configs = get_author_configs()
    for author in author_configs:
        if orcid is not None:
            if author["orcid"] == orcid:
                return author
        else:
            if author["family"] == family and author["given"] == given:
                return author
    return {}


def get_abstract_from_config(doi: str) -> str:
    paper_configs = get_paper_configs()
    papers = [p for p in paper_configs if p["doi"] == doi]
    if len(papers) > 0:
        return papers[0]["abstract"]
    return ""


def get_authors_with_categories() -> list[dict]:
    authors = []
    for author in get_author_configs():
        if author.get("categories"):
            authors.append(author)
    return authors
