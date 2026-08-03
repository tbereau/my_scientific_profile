import logging
from functools import lru_cache

import my_scientific_profile.utils  # noqa
from my_scientific_profile.utils.http import fetch_text

logger = logging.getLogger(__name__)


@lru_cache()
def fetch_bib(doi: str) -> str | None:
    """Return a BibTeX entry via DOI content negotiation, or None if there is none.

    Both Crossref and DataCite serve BibTeX this way, so arXiv and Zenodo DOIs
    resolve too, though as @misc rather than a venue-aware entry type.
    """
    logger.info(f"fetching bibtex for {doi}")
    bibtex = fetch_text(
        f"https://dx.doi.org/{doi}",
        provider="doi2bib",
        headers={"Accept": "application/x-bibtex"},
    )
    if bibtex is None:
        return None
    return bibtex.strip() or None
