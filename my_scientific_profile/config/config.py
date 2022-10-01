import logging
import os

import yaml
from yaml import YAMLObject

from my_scientific_profile.utils import ROOT_DIR

__all__ = ["CONFIG_PATH", "get_author_configs", "find_author_in_config"]

logger = logging.getLogger(__name__)

CONFIG_PATH = os.path.join(ROOT_DIR, "config")


def get_author_configs() -> list:
    with open(os.path.join(CONFIG_PATH, "authors.yaml"), "r") as stream:
        try:
            config = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            logger.error(f"error in configuration file")
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
