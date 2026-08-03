import logging

from my_scientific_profile.papers.open_access import open_access_from_unpaywall
from my_scientific_profile.papers.work_id import WorkId
from my_scientific_profile.providers.base import PartialRecord
from my_scientific_profile.unpaywall.works import get_unpaywall_work_by_doi

__all__ = ["UnpaywallProvider"]

logger = logging.getLogger(__name__)


class UnpaywallProvider:
    """Unpaywall, kept as a second opinion on availability.

    OpenAlex ingests Unpaywall's data and answers for nearly every DOI, so this
    normally makes no request at all. It earns its place when OpenAlex has not
    indexed a work yet, which happens with freshly minted DOIs.
    """

    name = "unpaywall"

    def supports(self, work_id: WorkId) -> bool:
        # Unpaywall indexes Crossref DOIs only.
        return work_id.is_crossref_doi

    def should_fetch(self, work_id: WorkId, collected: dict) -> bool:
        openalex = collected.get("openalex")
        return openalex is None or openalex.open_access is None

    def fetch(self, work_id: WorkId) -> PartialRecord | None:
        work = get_unpaywall_work_by_doi(work_id.doi)
        if work is None:
            return None
        return PartialRecord(
            provider=self.name,
            venue_name=work.journal_name,
            open_access=open_access_from_unpaywall(work),
        )
