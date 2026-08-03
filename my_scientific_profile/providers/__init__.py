"""Metadata providers and the rules for merging what they return.

No single service describes every publication: Crossref covers its members'
journals, DataCite covers arXiv and Zenodo, DBLP covers computer science
conferences, and OpenAlex covers most of everything but names proceedings
poorly. Each provider here reports only what it knows, and `merge` decides
which of them wins each field.
"""

from my_scientific_profile.providers.base import MetadataProvider, PartialRecord
from my_scientific_profile.providers.merge import (
    MERGE_ORDER,
    ResolvedRecord,
    resolve_record,
)

__all__ = [
    "MetadataProvider",
    "PartialRecord",
    "MERGE_ORDER",
    "ResolvedRecord",
    "resolve_record",
]
