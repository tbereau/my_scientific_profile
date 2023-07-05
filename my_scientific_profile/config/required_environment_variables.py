import logging

from decouple import config as environ, UndefinedValueError

from my_scientific_profile.config.util import get_config

logger = logging.getLogger(__name__)


def get_required_environment_variables(feature: str) -> list[str]:
    config = get_config("required_environment_variables.yaml")
    return [e for e in config[feature]]


def assert_all_environment_variables(feature: str) -> None:
    for variable in get_required_environment_variables(feature):
        try:
            assert environ(variable)
        except UndefinedValueError as e:
            logger.error(f"Missing environment variable {variable}")
            raise e
