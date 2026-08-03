#!/usr/bin/env python

"""Schema contract tests for `Paper`.

The personal website consumes papers three ways, and two of them are schema
contracts rather than function calls:

* `to_yaml` output feeds the CV;
* `convert_papers_to_dataframe` column names are quoted as literal strings in
  `research_landscape.qmd` and in `embed_papers.py`;
* S3 records are revived with `Paper(**record)`, so every field added later
  needs a default or previously stored papers stop loading.

These tests run offline: they build papers directly instead of calling any API.
"""

import datetime as dt
import io
import json
import os
import unittest
from dataclasses import asdict

import pandas as pd
from bson.json_util import dumps as mongo_dumps
from bson.json_util import loads as mongo_loads

# The package asserts this at import time; tests never reach the network.
os.environ.setdefault("ORCID_CODE", "offline-test-token")

from my_scientific_profile.authors.authors import Affiliation, Author  # noqa: E402
from my_scientific_profile.database.papers import (  # noqa: E402
    convert_papers_to_dataframe,
)
from my_scientific_profile.papers.open_access import OpenAccessPaperInfo  # noqa: E402
from my_scientific_profile.papers.papers import (  # noqa: E402
    Embedding,
    JournalInfo,
    Paper,
    VenueInfo,
    VenueKind,
    _drop_superseded_preprints,
)
from my_scientific_profile.papers.work_id import WorkId  # noqa: E402
from my_scientific_profile.utils.singletons import PaperSingleton  # noqa: E402

# Column names quoted as strings in research_landscape.qmd and embed_papers.py.
# Renaming a Paper field breaks the site silently; adding one is harmless.
WEBSITE_REQUIRED_COLUMNS = frozenset(
    {
        "doi",
        "title",
        "abstract",
        "year",
        "journal.name",
        "journal.volume",
        "journal.abbreviation",
        "embedding.x",
        "embedding.y",
        "embedding.topic_number",
        "embedding.topic_name",
    }
)

# The full set, so an accidental rename fails loudly rather than quietly.
# Update deliberately, together with the website, never to make a test pass.
# Excludes provenance, whose keys vary with which providers answered.
EXPECTED_COLUMNS = WEBSITE_REQUIRED_COLUMNS | {
    "publication_date",
    "authors",
    "citation_count",
    "bib_entry",
    "tldr",
    "journal.url",
    "journal.kind",
    "journal.issue",
    "journal.pages",
    "open_access.is_open_access",
    "open_access.open_access_status",
    "open_access.landing_page_url",
    "open_access.pdf_url",
    "work_id.scheme",
    "work_id.value",
}

LEGACY_S3_RECORD = {
    "doi": "10.1140/epjst/e2016-60114-5",
    "title": "Concurrent parametrization against static and kinetic information",
    "journal": {
        # No "kind": this is what records serialised before venues had one hold.
        "name": "The European Physical Journal Special Topics",
        "url": "http://dx.doi.org/10.1140/epjst/e2016-60114-5",
        "issue": "8-9",
        "abbreviation": "Eur. Phys. J. Spec. Top.",
        "pages": "1373-1389",
        "volume": 225,  # stored as an int, which pydantic v2 will not widen
    },
    "publication_date": dt.datetime(2016, 7, 15, 7, 35, 24),
    "authors": [
        {
            "given": "J.F.",
            "family": "Rudzinski",
            "affiliation": {"name": None, "city": None, "country": None},
            "orcid": None,
            "email": None,
            "full_name": "J.F. Rudzinski",
            "uuid": "bdc74bb4-1b51-11ee-b8f8-a2a06772f9f1",
        }
    ],
    "citation_count": 17,
    "open_access": {
        "is_open_access": True,
        "open_access_status": "green",
        "landing_page_url": "http://arxiv.org/abs/1607.05492",
        "pdf_url": "http://arxiv.org/pdf/1607.05492",
    },
    "bib_entry": "@article{Rudzinski_2016}",
    "abstract": "An abstract.",
    "tldr": "A tldr.",
    "year": 2016,
    "embedding": None,
}


def make_paper(doi: str, journal: VenueInfo, **overrides) -> Paper:
    fields = {
        "doi": doi,
        "title": "A  title   with   loose spacing",
        "journal": journal,
        "publication_date": dt.datetime(2026, 4, 1),
        "authors": [
            Author(given="ada", family="lovelace", affiliation=Affiliation()),
        ],
        "citation_count": 3,
        "open_access": OpenAccessPaperInfo(
            True, "green", "https://x/lp", "https://x/p"
        ),
        "bib_entry": "@inproceedings{x}",
        "abstract": "An abstract.",
        "tldr": "A tldr.",
        "embedding": Embedding(x=1.0, y=2.0, topic_number=0, topic_name="flows"),
    }
    fields.update(overrides)
    return Paper(**fields)


class TestVenueInfo(unittest.TestCase):
    def test_journal_info_is_still_importable_as_an_alias(self):
        self.assertIs(JournalInfo, VenueInfo)

    def test_kind_defaults_to_journal_for_records_that_predate_it(self):
        self.assertEqual(VenueInfo(url="https://x").kind, VenueKind.JOURNAL)

    def test_integer_volumes_are_accepted_and_normalised(self):
        self.assertEqual(VenueInfo(url="https://x", volume=225).volume, "225")

    def test_conference_venue_needs_no_volume_or_issue(self):
        venue = VenueInfo(
            url="https://proceedings.mlr.press/v267/",
            kind=VenueKind.CONFERENCE,
            name="AISTATS",
        )
        self.assertEqual(venue.kind, VenueKind.CONFERENCE)
        self.assertIsNone(venue.volume)

    def test_kind_serialises_as_its_plain_value(self):
        # The CSV and the JSON both go through str()/json, so the enum must not
        # leak its repr into the data the website reads.
        self.assertEqual(str(VenueKind.CONFERENCE), "conference")
        self.assertEqual(f"{VenueKind.PREPRINT}", "preprint")


class TestPaperSchema(unittest.TestCase):
    def setUp(self):
        PaperSingleton._instances.clear()

    def test_legacy_s3_record_still_loads(self):
        paper = Paper(**LEGACY_S3_RECORD)
        self.assertEqual(paper.journal.kind, VenueKind.JOURNAL)
        self.assertEqual(paper.journal.volume, "225")
        self.assertEqual(paper.year, 2016)

    def test_dataframe_exposes_every_column_the_website_quotes(self):
        paper = make_paper("10.0/journal", VenueInfo(url="https://x", volume=225))
        columns = set(convert_papers_to_dataframe([paper]).columns)
        self.assertEqual(WEBSITE_REQUIRED_COLUMNS - columns, set())

    def test_dataframe_columns_are_stable(self):
        paper = make_paper(
            "10.0/journal",
            VenueInfo(url="https://x", volume=225),
            work_id=WorkId(scheme="doi", value="10.0/journal"),
        )
        columns = {
            column
            for column in convert_papers_to_dataframe([paper]).columns
            if not column.startswith("provenance")
        }
        self.assertEqual(columns, EXPECTED_COLUMNS)

    def test_missing_bib_entry_is_allowed(self):
        paper = make_paper(
            "10.0/nobib", VenueInfo(url="https://x"), bib_entry=None
        )
        self.assertIsNone(paper.bib_entry)

    def test_kind_reaches_the_website_as_a_plain_value(self):
        paper = make_paper(
            "10.0/conf",
            VenueInfo(url="https://x", kind=VenueKind.CONFERENCE, name="AISTATS"),
        )
        frame = convert_papers_to_dataframe([paper])
        reloaded = pd.read_csv(io.StringIO(frame.to_csv(index=False)))
        self.assertEqual(reloaded["journal.kind"][0], "conference")
        self.assertEqual(json.loads(frame.to_json())["journal.kind"]["0"], "conference")

    def test_s3_round_trip_preserves_the_venue(self):
        paper = make_paper(
            "10.0/conf",
            VenueInfo(url="https://x", kind=VenueKind.CONFERENCE, name="AISTATS"),
            work_id=WorkId(scheme="arxiv", value="2511.01464"),
            provenance={"venue_name": "config", "abstract": "openalex"},
        )
        stored = mongo_dumps([asdict(paper)])
        PaperSingleton._instances.clear()
        revived = [Paper(**record) for record in mongo_loads(stored)]
        self.assertEqual(revived[0].journal.kind, VenueKind.CONFERENCE)
        self.assertEqual(revived[0].journal.name, "AISTATS")
        self.assertEqual(revived[0].work_id.key, "arxiv:2511.01464")
        self.assertEqual(revived[0].source_of("venue_name"), "config")

    def test_records_without_the_new_fields_still_load(self):
        # Papers stored before work identity and provenance existed.
        paper = Paper(**LEGACY_S3_RECORD)
        self.assertIsNone(paper.work_id)
        self.assertIsNone(paper.source_of("abstract"))


class TestSupersededPreprints(unittest.TestCase):
    """An ORCID record lists preprints beside the papers they became."""

    def setUp(self):
        PaperSingleton._instances.clear()

    def journal(self, doi, title, when):
        return make_paper(
            doi,
            VenueInfo(url="https://x", kind=VenueKind.JOURNAL, name="J"),
            title=title,
            publication_date=when,
        )

    def preprint(self, doi, title, when):
        return make_paper(
            doi,
            VenueInfo(url="https://x", kind=VenueKind.PREPRINT, name="ChemRxiv"),
            title=title,
            publication_date=when,
        )

    def test_preprint_yields_to_its_published_version(self):
        published = self.journal(
            "10.0/j",
            "Roadmap on data-centric materials science",
            dt.datetime(2024, 6, 1),
        )
        preprint = self.preprint(
            "10.0/p",
            "Roadmap on Data-Centric Materials Science",
            dt.datetime(2024, 2, 1),
        )
        kept = _drop_superseded_preprints([published, preprint])
        self.assertEqual([p.doi for p in kept], ["10.0/j"])

    def test_only_the_newest_revision_of_an_unpublished_preprint_survives(self):
        newer = self.preprint("10.0/v3", "Some Preprint", dt.datetime(2025, 3, 1))
        older = self.preprint("10.0/v2", "Some preprint", dt.datetime(2025, 1, 1))
        kept = _drop_superseded_preprints([newer, older])
        self.assertEqual([p.doi for p in kept], ["10.0/v3"])

    def test_spelling_differences_do_not_defeat_superseding(self):
        # The real pair from the ORCID record: "parameterization" in the
        # preprint, "Parametrization" in the journal version.
        published = self.journal(
            "10.1021/acs.jctc.5c01178",
            "Fast Parametrization of Martini3 Models for Fragments and Small Molecules",
            dt.datetime(2025, 11, 1),
        )
        preprint = self.preprint(
            "10.1101/2025.07.13.664596",
            "Fast parameterization of Martini3 models for fragments"
            " and small molecules",
            dt.datetime(2025, 7, 18),
        )
        kept = _drop_superseded_preprints([published, preprint])
        self.assertEqual([p.doi for p in kept], ["10.1021/acs.jctc.5c01178"])

    def test_merely_similar_titles_are_left_alone(self):
        # Two genuinely distinct works on the record, measured at 0.81.
        published = self.journal(
            "10.0/j",
            "Shared metadata for data-centric materials science",
            dt.datetime(2023, 1, 1),
        )
        preprint = self.preprint(
            "10.0/p",
            "Roadmap on data-centric materials science",
            dt.datetime(2024, 2, 1),
        )
        kept = _drop_superseded_preprints([published, preprint])
        self.assertEqual(len(kept), 2)

    def test_two_published_works_are_never_merged(self):
        first = self.journal("10.0/a", "Same Title", dt.datetime(2020, 1, 1))
        second = self.journal("10.0/b", "Same title", dt.datetime(2021, 1, 1))
        kept = _drop_superseded_preprints([first, second])
        self.assertEqual(len(kept), 2)

    def test_an_unpublished_preprint_is_kept(self):
        preprint = self.preprint("10.0/only", "Novel Work", dt.datetime(2026, 1, 1))
        self.assertEqual(len(_drop_superseded_preprints([preprint])), 1)


class TestToYaml(unittest.TestCase):
    def setUp(self):
        PaperSingleton._instances.clear()

    def test_journal_paper_yaml_is_unchanged(self):
        paper = make_paper(
            "10.0/journal",
            VenueInfo(
                url="https://x",
                name="Journal of Things",
                abbreviation="J. Things",
                volume=225,
            ),
        )
        self.assertEqual(
            paper.to_yaml(),
            """- authors: Ada Lovelace
  title: "A title with loose spacing"
  journal: "J. Things"
  volume: 225
  year: 2026
  open_access_flag: True
  open_access_url: https://x/lp
  open_access_pdf: https://x/p
  doi: "10.0/journal"
""",
        )

    def test_nameless_preprint_yaml_leaves_blanks_rather_than_none(self):
        paper = make_paper(
            "10.0/preprint",
            VenueInfo(url="https://x", kind=VenueKind.PREPRINT),
        )
        self.assertIn('journal: ""', paper.to_yaml())
        self.assertIn("volume: \n", paper.to_yaml())
        self.assertNotIn("None", paper.to_yaml())


if __name__ == "__main__":
    unittest.main()
