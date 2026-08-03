import logging

from my_scientific_profile.orcid.detailed_work import get_detailed_work
from my_scientific_profile.orcid.works import get_work_id_to_put_code_map
from my_scientific_profile.papers.venue import VenueKind
from my_scientific_profile.papers.work_id import WorkId
from my_scientific_profile.providers.base import PartialRecord

__all__ = ["OrcidProvider", "ORCID_VENUE_KINDS"]

logger = logging.getLogger(__name__)

ORCID_VENUE_KINDS = {
    "journal-article": VenueKind.JOURNAL,
    "conference-paper": VenueKind.CONFERENCE,
    "conference-abstract": VenueKind.CONFERENCE,
    "conference-poster": VenueKind.CONFERENCE,
    "preprint": VenueKind.PREPRINT,
    "data-set": VenueKind.REPOSITORY,
    "software": VenueKind.REPOSITORY,
    "book": VenueKind.BOOK,
    "book-chapter": VenueKind.BOOK,
}


class OrcidProvider:
    """The author's own ORCID record.

    Thin on metadata, but it is the only provider that reflects what the author
    says a work is, which matters for conference papers no indexer has yet.
    """

    name = "orcid"

    def __init__(self, orcid_id: str | None = None) -> None:
        self.orcid_id = orcid_id

    def supports(self, work_id: WorkId) -> bool:
        return work_id in get_work_id_to_put_code_map(self.orcid_id)

    def fetch(self, work_id: WorkId) -> PartialRecord | None:
        put_code = get_work_id_to_put_code_map(self.orcid_id).get(work_id)
        if put_code is None:
            return None
        work = get_detailed_work(put_code, orcid_id=self.orcid_id)
        if work is None:
            return None
        return PartialRecord(
            provider=self.name,
            title=work.title.title.value if work.title else None,
            venue_kind=ORCID_VENUE_KINDS.get(work.type),
            venue_name=work.journal_title.value if work.journal_title else None,
            url=work.url.value if work.url else None,
            publication_date=(
                work.publication_date.datetime if work.publication_date else None
            ),
        )
