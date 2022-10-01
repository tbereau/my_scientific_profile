import logging
import os

__all__ = ["ROOT_DIR"]

logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

logger_blocklist = ["urllib3", "matplotlib"]
for module in logger_blocklist:
    logging.getLogger(module).setLevel(logging.WARNING)

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
