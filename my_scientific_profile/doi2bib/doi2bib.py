import logging
from functools import lru_cache
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import my_scientific_profile.utils  # noqa

logger = logging.getLogger(__name__)


@lru_cache()
def fetch_bib(doi: str) -> str:
    logger.info(f"fetching doi2bib for {doi}")
    url = f"https://dx.doi.org/{doi}"
    request = Request(url)
    request.add_header("Accept", "application/x-bibtex")
    try:
        with urlopen(request) as f:
            bibtex = f.read().decode()
    except HTTPError as e:
        if e.code == 404:
            raise ValueError("DOI not found.")
        else:
            raise ValueError("Service unavailable.")
    return bibtex
