import logging
from dataclasses import replace

from my_scientific_profile.papers.work_id import WorkId
from my_scientific_profile.providers.base import (
    RECORD_FIELDS,
    MetadataProvider,
    PartialRecord,
)
from my_scientific_profile.providers.bibtex import Doi2BibProvider
from my_scientific_profile.providers.crossref import CrossrefProvider
from my_scientific_profile.providers.datacite import DataCiteProvider
from my_scientific_profile.providers.dblp import DblpProvider
from my_scientific_profile.providers.openalex import OpenAlexProvider
from my_scientific_profile.providers.orcid import OrcidProvider
from my_scientific_profile.providers.overrides import ConfigProvider
from my_scientific_profile.providers.semantic_scholar import SemanticScholarProvider
from my_scientific_profile.providers.unpaywall import UnpaywallProvider
from my_scientific_profile.utils.http import ProviderUnavailable

__all__ = [
    "MERGE_ORDER",
    "ResolvedRecord",
    "resolve_record",
    "primary_providers",
    "refining_providers",
]

logger = logging.getLogger(__name__)

# Which provider wins each field, best first. Trust is per field rather than
# per provider: DBLP names a machine learning conference correctly but has no
# abstract, Semantic Scholar is the reverse, and OpenAlex is the only one that
# speaks for every DOI. Reordering trust is an edit here, not a code change.
MERGE_ORDER: dict[str, tuple[str, ...]] = {
    "title": (
        "config",
        "crossref",
        "openalex",
        "datacite",
        "semantic_scholar",
        "orcid",
    ),
    "venue_kind": ("config", "dblp", "crossref", "orcid", "openalex", "datacite"),
    # ORCID beats OpenAlex on names because it is hand-curated: for a
    # repository it says "Zenodo" where OpenAlex says "Zenodo (CERN European
    # Organization for Nuclear Research)". Crossref still leads for journals.
    "venue_name": (
        "config",
        "dblp",
        "crossref",
        "orcid",
        "openalex",
        "datacite",
        "unpaywall",
    ),
    "venue_abbreviation": ("config", "dblp", "crossref", "openalex"),
    "volume": ("config", "crossref", "dblp", "openalex"),
    "issue": ("config", "crossref", "openalex"),
    "pages": ("config", "crossref", "dblp", "openalex"),
    "url": ("config", "crossref", "orcid", "dblp", "openalex", "datacite"),
    "publication_date": ("config", "crossref", "openalex", "datacite", "orcid"),
    # Crossref stays first for authors: its list feeds the ORCID name lookup
    # that the collaborator pages are built from.
    "authors": ("crossref", "openalex", "datacite"),
    "citation_count": ("openalex", "crossref", "datacite"),
    "abstract": ("config", "semantic_scholar", "crossref", "openalex", "datacite"),
    "tldr": ("semantic_scholar",),
    "bib_entry": ("config", "doi2bib"),
    "open_access": ("openalex", "unpaywall"),
}


class ResolvedRecord:
    """A merged record together with the provider behind each field."""

    def __init__(
        self,
        record: PartialRecord,
        provenance: dict[str, str],
        outages: list[tuple[str, str]],
    ) -> None:
        self.record = record
        self.provenance = provenance
        self.outages = outages

    @property
    def providers_used(self) -> list[str]:
        return sorted(set(self.provenance.values()))


def primary_providers(orcid_id: str | None = None) -> tuple[MetadataProvider, ...]:
    """Providers queried by identifier, for every work."""
    return (
        ConfigProvider(),
        OrcidProvider(orcid_id),
        CrossrefProvider(),
        DataCiteProvider(),
        OpenAlexProvider(),
        # After OpenAlex, which usually leaves it nothing to add.
        UnpaywallProvider(),
        SemanticScholarProvider(),
        Doi2BibProvider(),
    )


def refining_providers() -> tuple:
    """Providers consulted only once a first pass leaves something missing."""
    return (DblpProvider(),)


def resolve_record(work_id: WorkId, orcid_id: str | None = None) -> ResolvedRecord:
    """Gather every provider's view of a work and merge it field by field."""
    records: dict[str, PartialRecord] = {}
    outages: list[tuple[str, str]] = []

    for provider in primary_providers(orcid_id):
        _collect(provider, work_id, records, outages)

    merged, provenance = _merge(records)
    for provider in refining_providers():
        if not provider.should_refine(work_id, merged):
            continue
        try:
            if record := provider.refine(work_id, merged):
                records[provider.name] = record
        except ProviderUnavailable as error:
            logger.warning(f"{work_id.key}: {error}")
            outages.append((provider.name, str(error)))
    if len(records) > len(provenance):
        merged, provenance = _merge(records)

    return ResolvedRecord(merged, provenance, outages)


def _collect(
    provider: MetadataProvider,
    work_id: WorkId,
    records: dict[str, PartialRecord],
    outages: list[tuple[str, str]],
) -> None:
    if not provider.supports(work_id):
        return
    # A provider may also decline once it sees what has already answered. This
    # decides only whether a request is worth making; who wins each field is
    # still settled by MERGE_ORDER, not by the order providers run in.
    should_fetch = getattr(provider, "should_fetch", None)
    if should_fetch is not None and not should_fetch(work_id, records):
        return
    try:
        if record := provider.fetch(work_id):
            records[provider.name] = record
    except ProviderUnavailable as error:
        # An outage costs the fields this provider would have supplied. It must
        # not cost the paper, and it must not pass unrecorded.
        logger.warning(f"{work_id.key}: {error}")
        outages.append((provider.name, str(error)))


def _merge(
    records: dict[str, PartialRecord]
) -> tuple[PartialRecord, dict[str, str]]:
    merged = PartialRecord(provider="merged")
    provenance: dict[str, str] = {}
    for field in RECORD_FIELDS:
        order = MERGE_ORDER.get(field, tuple(records))
        for provider_name in order:
            record = records.get(provider_name)
            if record is None:
                continue
            value = getattr(record, field)
            if value is None or value == "":
                continue
            merged = replace(merged, **{field: value})
            provenance[field] = provider_name
            break
    return merged, provenance
