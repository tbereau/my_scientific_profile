#!/usr/bin/env python

"""Tests for work identity and the provider merge rules.

All offline: providers are replaced with stubs so the merge order can be
checked without a network, which is the point of separating the two.
"""

import datetime as dt
import os
import unittest

os.environ.setdefault("ORCID_CODE", "offline-test-token")

from my_scientific_profile.papers.venue import VenueKind  # noqa: E402
from my_scientific_profile.papers.work_id import WorkId  # noqa: E402
from my_scientific_profile.providers import merge as merge_module  # noqa: E402
from my_scientific_profile.providers.base import (  # noqa: E402
    RECORD_FIELDS,
    AuthorRef,
    PartialRecord,
    split_display_name,
)
from my_scientific_profile.providers.dblp import DblpProvider  # noqa: E402
from my_scientific_profile.providers.merge import (  # noqa: E402
    MERGE_ORDER,
    resolve_record,
)
from my_scientific_profile.providers.openalex import (  # noqa: E402
    reconstruct_abstract,
)
from my_scientific_profile.utils.http import ProviderUnavailable  # noqa: E402


class StubProvider:
    def __init__(self, name, record=None, error=None, supports=True):
        self.name = name
        self._record = record
        self._error = error
        self._supports = supports
        self.fetch_calls = 0

    def supports(self, work_id):
        return self._supports

    def fetch(self, work_id):
        self.fetch_calls += 1
        if self._error:
            raise self._error
        return self._record


class TestWorkId(unittest.TestCase):
    def test_a_plain_doi_stays_a_doi(self):
        work_id = WorkId.from_doi("10.1140/epjst/e2016-60114-5")
        self.assertEqual(work_id.scheme, "doi")
        self.assertTrue(work_id.is_crossref_doi)

    def test_an_arxiv_doi_is_recognised_as_an_arxiv_id(self):
        work_id = WorkId.from_doi("10.48550/arXiv.2511.01464")
        self.assertEqual(work_id.scheme, "arxiv")
        self.assertEqual(work_id.value, "2511.01464")

    def test_an_arxiv_id_still_yields_a_resolvable_doi(self):
        work_id = WorkId(scheme="arxiv", value="2511.01464")
        self.assertEqual(work_id.doi, "10.48550/arXiv.2511.01464")

    def test_datacite_prefixes_are_not_offered_to_crossref(self):
        # Asking Crossref about these wastes a request on every paper.
        self.assertFalse(WorkId.from_doi("10.48550/arXiv.2511.01464").is_crossref_doi)
        self.assertFalse(WorkId.from_doi("10.5281/zenodo.15446343").is_crossref_doi)
        self.assertTrue(WorkId.from_doi("10.1021/acs.jctc.5c01178").is_crossref_doi)

    def test_scopus_and_pubmed_identifiers_are_refused(self):
        # They identify the work to somebody, but to no provider we can query.
        self.assertIsNone(WorkId.from_external_id("eid", "2-s2.0-84961291234"))
        self.assertIsNone(WorkId.from_external_id("pmid", "12345678"))

    def test_bare_arxiv_identifiers_are_read(self):
        for raw in ("2511.01464", "arXiv:2511.01464", "2511.01464v2"):
            work_id = WorkId.from_external_id("arxiv", raw)
            self.assertIsNotNone(work_id, raw)
            self.assertEqual(work_id.scheme, "arxiv")

    def test_config_style_keys_round_trip(self):
        self.assertEqual(WorkId.parse("arxiv:2511.01464").scheme, "arxiv")
        self.assertEqual(WorkId.parse("10.1021/x").scheme, "doi")
        self.assertEqual(WorkId(scheme="arxiv", value="2511.01464").key,
                         "arxiv:2511.01464")


class TestMergeOrder(unittest.TestCase):
    def test_every_field_declares_a_trust_order(self):
        self.assertEqual([f for f in RECORD_FIELDS if f not in MERGE_ORDER], [])

    def test_orders_only_name_providers_that_exist(self):
        known = {p.name for p in merge_module.primary_providers()}
        known |= {p.name for p in merge_module.refining_providers()}
        known.add("rendered")
        for field, order in MERGE_ORDER.items():
            for provider in order:
                self.assertIn(provider, known, f"{field} names unknown {provider}")


class TestResolveRecord(unittest.TestCase):
    def setUp(self):
        self.work_id = WorkId.from_doi("10.0/x")
        self._primary = merge_module.primary_providers
        self._refining = merge_module.refining_providers
        merge_module.refining_providers = lambda: ()

    def tearDown(self):
        merge_module.primary_providers = self._primary
        merge_module.refining_providers = self._refining

    def use(self, *providers):
        merge_module.primary_providers = lambda orcid_id=None: providers

    def test_the_field_order_decides_not_the_provider_order(self):
        # DBLP is trusted for a venue name and Crossref for a volume, so a
        # single record must be able to lose one field and win another.
        self.use(
            StubProvider(
                "crossref",
                PartialRecord("crossref", venue_name="arXiv", volume="7"),
            ),
            StubProvider("dblp", PartialRecord("dblp", venue_name="AISTATS")),
        )
        resolved = resolve_record(self.work_id)
        self.assertEqual(resolved.record.venue_name, "AISTATS")
        self.assertEqual(resolved.record.volume, "7")
        self.assertEqual(resolved.provenance["venue_name"], "dblp")
        self.assertEqual(resolved.provenance["volume"], "crossref")

    def test_config_outranks_every_service(self):
        self.use(
            StubProvider("crossref", PartialRecord("crossref", title="Wrong")),
            StubProvider("config", PartialRecord("config", title="Right")),
        )
        resolved = resolve_record(self.work_id)
        self.assertEqual(resolved.record.title, "Right")

    def test_an_outage_costs_a_field_not_the_record(self):
        self.use(
            StubProvider("crossref", PartialRecord("crossref", title="Kept")),
            StubProvider(
                "semantic_scholar",
                error=ProviderUnavailable("semantic_scholar", "429"),
            ),
        )
        resolved = resolve_record(self.work_id)
        self.assertEqual(resolved.record.title, "Kept")
        self.assertIsNone(resolved.record.tldr)
        self.assertEqual([p for p, _ in resolved.outages], ["semantic_scholar"])

    def test_unsupported_providers_are_never_called(self):
        skipped = StubProvider("crossref", supports=False)
        self.use(skipped)
        resolve_record(self.work_id)
        self.assertEqual(skipped.fetch_calls, 0)

    def test_empty_values_do_not_win_a_field(self):
        self.use(
            StubProvider("crossref", PartialRecord("crossref", venue_name="")),
            StubProvider("openalex", PartialRecord("openalex", venue_name="arXiv")),
        )
        self.assertEqual(resolve_record(self.work_id).record.venue_name, "arXiv")

    def test_authors_stay_references_until_one_provider_wins(self):
        # Building an Author costs an ORCID search, so the losing provider's
        # authors must never be built.
        self.use(
            StubProvider(
                "crossref",
                PartialRecord("crossref", authors=(AuthorRef("Bereau", "Tristan"),)),
            ),
            StubProvider(
                "openalex",
                PartialRecord("openalex", authors=(AuthorRef("Wrong", "Person"),)),
            ),
        )
        resolved = resolve_record(self.work_id)
        self.assertEqual([a.family for a in resolved.record.authors], ["Bereau"])


class TestDblpRefinement(unittest.TestCase):
    def setUp(self):
        self.provider = DblpProvider()
        self.work_id = WorkId.from_doi("10.48550/arXiv.2511.01464")

    def test_refines_a_work_that_still_looks_unpublished(self):
        record = PartialRecord(
            "merged", title="Split-Flows", venue_kind=VenueKind.PREPRINT
        )
        self.assertTrue(self.provider.should_refine(self.work_id, record))

    def test_leaves_a_journal_article_alone(self):
        # A title search of a computer science bibliography invites false
        # matches, so it is only worth running when something is missing.
        record = PartialRecord(
            "merged", title="Some chemistry", venue_kind=VenueKind.JOURNAL
        )
        self.assertFalse(self.provider.should_refine(self.work_id, record))

    def test_needs_a_title_to_search_with(self):
        record = PartialRecord("merged", venue_kind=VenueKind.PREPRINT)
        self.assertFalse(self.provider.should_refine(self.work_id, record))

    def test_is_never_queried_by_identifier(self):
        self.assertFalse(self.provider.supports(self.work_id))


class TestHelpers(unittest.TestCase):
    def test_openalex_abstracts_are_rebuilt_in_order(self):
        inverted = {"transport": [1], "Measure": [0], "loss": [2]}
        self.assertEqual(reconstruct_abstract(inverted), "Measure transport loss")

    def test_a_missing_abstract_stays_missing(self):
        self.assertIsNone(reconstruct_abstract(None))
        self.assertIsNone(reconstruct_abstract({}))

    def test_display_names_split_on_the_last_word(self):
        self.assertEqual(
            split_display_name("Sander Hummerich"), ("Sander", "Hummerich")
        )
        self.assertEqual(split_display_name("Jean-Paul van der Berg")[1], "Berg")
        self.assertEqual(split_display_name("Prince"), ("", "Prince"))
        self.assertEqual(split_display_name(""), ("", ""))


class TestBibEntryRendering(unittest.TestCase):
    def test_a_conference_paper_is_cited_as_inproceedings(self):
        # Content negotiation returns @misc for an arXiv DOI, which cites a
        # preprint rather than the conference the work appeared at.
        from my_scientific_profile.authors.authors import Affiliation, Author
        from my_scientific_profile.papers.papers import Paper
        from my_scientific_profile.papers.open_access import no_open_access_info
        from my_scientific_profile.papers.venue import VenueInfo
        from my_scientific_profile.providers.bibtex import render_bib_entry
        from my_scientific_profile.utils.singletons import PaperSingleton

        PaperSingleton._instances.clear()
        paper = Paper(
            doi="10.48550/arXiv.2511.01464",
            title="Split-Flows",
            journal=VenueInfo(
                url="https://proceedings.mlr.press/v267/",
                kind=VenueKind.CONFERENCE,
                name="AISTATS",
                volume="267",
            ),
            publication_date=dt.datetime(2026, 5, 2),
            authors=[
                Author(given="sander", family="hummerich", affiliation=Affiliation())
            ],
            citation_count=1,
            open_access=no_open_access_info(),
        )
        entry = render_bib_entry(paper)
        self.assertTrue(entry.startswith("@inproceedings{hummerich_2026,"))
        self.assertIn("booktitle = {AISTATS}", entry)
        self.assertIn("volume = {267}", entry)
        self.assertNotIn("journal =", entry)


if __name__ == "__main__":
    unittest.main()
