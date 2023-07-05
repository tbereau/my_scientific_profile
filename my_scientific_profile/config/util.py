import logging
import os
import yaml

from my_scientific_profile.utils.utils import ROOT_DIR

logger = logging.getLogger(__name__)

__all__ = ["CONFIG_PATH", "get_config"]


CONFIG_PATH = os.path.join(ROOT_DIR, "config")


def get_config(yaml_file: str) -> list | dict:
    with open(os.path.join(CONFIG_PATH, yaml_file), "r") as stream:
        try:
            config = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            logger.error(f"error in configuration file {yaml_file}")
            raise exc
    return config
