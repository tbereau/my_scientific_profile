import logging
import re

from pydantic.dataclasses import dataclass

__all__ = ["WorkId", "ARXIV_DOI_PREFIX", "DATACITE_DOI_PREFIXES"]

logger = logging.getLogger(__name__)

ARXIV_DOI_PREFIX = "10.48550"

# Registered with DataCite rather than Crossref, so Crossref and Unpaywall
# know nothing about them however well formed the DOI is.
DATACITE_DOI_PREFIXES = frozenset({ARXIV_DOI_PREFIX, "10.5281"})

# ORCID reports identifiers by type; these are the ones we can resolve, in the
# order we would rather have them. A Scopus eid or a PMID identifies the work
# to somebody, but not to any metadata provider we can query.
RESOLVABLE_ID_TYPES = ("doi", "arxiv")

_ARXIV_DOI_PATTERN = re.compile(rf"^{re.escape(ARXIV_DOI_PREFIX)}/arxiv\.(.+)$", re.I)
_ARXIV_BARE_PATTERN = re.compile(r"^(?:arxiv:)?(\d{4}\.\d{4,5}(?:v\d+)?)$", re.I)


@dataclass(frozen=True)
class WorkId:
    """A work's identity, which is not always a DOI.

    Conference proceedings in computer science are frequently published with no
    DOI at all, so identity has to carry its scheme rather than assume one.
    """

    scheme: str
    value: str

    @property
    def key(self) -> str:
        return f"{self.scheme}:{self.value}"

    @property
    def doi(self) -> str | None:
        """The DOI for this work, if the scheme implies one.

        arXiv mints a DOI for every submission, so an arXiv identifier is
        resolvable as a DOI even though nothing was published anywhere.
        """
        if self.scheme == "doi":
            return self.value
        if self.scheme == "arxiv":
            return f"{ARXIV_DOI_PREFIX}/arXiv.{self.value}"
        return None

    @property
    def is_crossref_doi(self) -> bool:
        doi = self.doi
        return doi is not None and doi.split("/")[0] not in DATACITE_DOI_PREFIXES

    @classmethod
    def from_doi(cls, doi: str) -> "WorkId":
        """Build an id from a DOI, recognising arXiv's DOIs as arXiv ids."""
        if match := _ARXIV_DOI_PATTERN.match(doi):
            return cls(scheme="arxiv", value=match.group(1))
        return cls(scheme="doi", value=doi)

    @classmethod
    def from_external_id(cls, id_type: str, value: str) -> "WorkId | None":
        """Build an id from one ORCID external identifier, or None if unusable."""
        id_type = (id_type or "").lower()
        value = (value or "").strip()
        if not value:
            return None
        if id_type == "doi":
            return cls.from_doi(value)
        if id_type == "arxiv":
            if match := _ARXIV_BARE_PATTERN.match(value):
                return cls(scheme="arxiv", value=match.group(1))
            logger.info(f"unrecognised arXiv identifier {value!r}")
            return None
        return None

    @classmethod
    def parse(cls, text: str) -> "WorkId":
        """Read a `scheme:value` id, as written in the config file."""
        scheme, _, value = text.partition(":")
        if not value:
            return cls.from_doi(text)
        return cls(scheme=scheme.strip().lower(), value=value.strip())
