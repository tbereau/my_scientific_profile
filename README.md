# My Scientific Profile

Programmatically retrieve information about your scientific publications from APIs. Your ORCID record decides which works are yours; a set of metadata providers then describes them. For best results, keep your publications listed on ORCID.

Providers, none of which is authoritative on its own:

| Provider | Contributes |
|---|---|
| ORCID | which works are yours, and what you say they are |
| CrossRef | journals: venue, volume, issue, pages, authors, abstract |
| DataCite | arXiv, Zenodo and anything else Crossref never registered |
| OpenAlex | open access status, citation counts, author ORCIDs — for every DOI |
| DBLP | computer science conference names, which carry no DOI to look up |
| Semantic Scholar | TL;DR, and abstracts the publisher withholds |
| doi2bib | BibTeX by DOI content negotiation |
| Unpaywall | a second opinion on availability, only when OpenAlex has no record |

The library generates `Paper` and `Author` objects that contain various information about a scientific publication and author, respectively.

### How a paper is resolved

Each provider reports only what it knows, as a `PartialRecord`. `providers/merge.py` then merges them **field by field**, using a declared trust order per field rather than per provider: DBLP wins a conference name, CrossRef wins a volume, Semantic Scholar wins a TL;DR. Reordering trust, or adding a provider, is an edit to `MERGE_ORDER`.

Two consequences worth knowing:

- A paper's `journal` field is a `VenueInfo` whose `kind` separates journal articles from conference papers, preprints and repository entries — only journal articles reliably have a volume and issue. `JournalInfo` remains as an alias.
- `paper.source_of("abstract")` reports which provider supplied a field, so a page can credit the right source instead of asserting a fixed pipeline.

A provider returning `None` means the work is absent there, which is routine. A provider that fails raises, costing its fields but never the paper — and the loss is recorded. Works that cannot be resolved at all raise `PaperResolutionError`; `fetch_all_paper_infos` collects those rather than dropping them, and `get_last_resolution_report()` lists everything skipped, collapsed or degraded on the last run.

Preprints are collapsed onto the published version they became, so a paper listed on ORCID as both does not appear twice.

### When no API knows

Conference proceedings are often published months after acceptance, and PMLR volumes carry no DOI at all, so for a while no provider can describe such a paper. The `papers:` section of the config overrides any field, and an entry written with `id:` also lists a work ORCID has not got yet:

```yaml
papers:
    -   id: "arxiv:2511.01464"
        publication_date: 2026-05-02
        venue:
            kind: conference
            name: "Proceedings of the 29th International Conference on Artificial Intelligence and Statistics"
            abbreviation: "AISTATS"
            volume: 267
            url: "https://proceedings.mlr.press/v267/"
```

Without `publication_date` the arXiv posting date stands in, which would date a paper presented in 2026 to 2025.

Delete the entry once DBLP lists the proceedings; the providers take over with no code change. `ignore: true` keeps a work off the list entirely.

### Noticing what is missing

`discovery.find_unlisted_works()` reports works OpenAlex attributes to your ORCID that your record does not list, comparing titles as well as identifiers so an already-listed paper is not reported twice. ORCID stays the authority — this only tells you what to consider adding.

This library is used to automatically generate all publication and collaborator information on my [personal website](https://tristanbereau.com) and [CV](https://tristanbereau.com/files/bereau_cv.pdf).

## Highlight

A paper can be queried simply by its DOI:
```python
from my_scientific_profile.papers.papers import fetch_paper_info
paper1 = fetch_paper_info("10.1140/epjst/e2016-60114-5")
```

Here's the content of `paper1`:

```python
Paper(doi='10.1140/epjst/e2016-60114-5', title='Concurrent parametrization against static and kinetic information leads to more robust coarse-grained force fields', journal=VenueInfo(url='https://doi.org/10.1140/epjst/e2016-60114-5', kind=<VenueKind.JOURNAL: 'journal'>, name='The European Physical Journal Special Topics', issue='8-9', abbreviation='Eur. Phys. J. Spec. Top.', pages='1373-1389', volume='225'), publication_date=datetime.datetime(2016, 7, 15, 7, 35, 24, tzinfo=TzInfo(UTC)), authors=[Author(given='J.F.', family='Rudzinski', affiliation=Affiliation(name=None, city=None, country=None), orcid=None, email=None, full_name='J.F. Rudzinski', uuid='bdc74bb4-1b51-11ee-b8f8-a2a06772f9f1'), Author(given='T.', family='Bereau', affiliation=Affiliation(name=None, city=None, country=None), orcid=None, email=None, full_name='T. Bereau', uuid='be2ca9be-1b51-11ee-b8f8-a2a06772f9f1')], citation_count=17, open_access=OpenAccessPaperInfo(is_open_access=True, open_access_status='green', landing_page_url='http://arxiv.org/abs/1607.05492', pdf_url='http://arxiv.org/pdf/1607.05492'), bib_entry='@article{Rudzinski_2016,\n\tdoi = {10.1140/epjst/e2016-60114-5},\n\turl = {https://doi.org/10.1140%2Fepjst%2Fe2016-60114-5},\n\tyear = 2016,\n\tmonth = {jul},\n\tpublisher = {Springer Science and Business Media {LLC}},\n\tvolume = {225},\n\tnumber = {8-9},\n\tpages = {1373--1389},\n\tauthor = {J.F. Rudzinski and T. Bereau},\n\ttitle = {Concurrent parametrization against static and kinetic information leads to more robust coarse-grained force fields},\n\tjournal = {The European Physical Journal Special Topics}\n}', abstract='The parametrization of coarse-grained (CG) simulation models for molecular systems often aims at reproducing static properties alone. The reduced molecular friction of the CG representation usually results in faster, albeit inconsistent, dynamics. In this work, we rely on Markov state models to simultaneously characterize the static and kinetic properties of two CG peptide force fields—one top-down and one bottom-up. Instead of a rigorous evolution of CG dynamics (e.g., using a generalized Langevin equation), we attempt to improve the description of kinetics by simply altering the existing CG models, which employ standard Langevin dynamics. By varying masses and relevant force-field parameters, we can improve the timescale separation of the slow kinetic processes, achieve a more consistent ratio of mean-first-passage times between metastable states, and refine the relative free-energies between these states. Importantly, we show that the incorporation of kinetic information into a structure-based parametrization improves the description of the helix-coil transition sampled by a minimal CG model. While structure-based models understabilize the helical state, kinetic constraints help identify CG models that improve the ratio of forward/backward timescales by effectively hindering the sampling of spurious conformational intermediate states.', tldr='This work relies on Markov state models to simultaneously characterize the static and kinetic properties of two CG peptide force fields—one top-down and one bottom-up—in order to improve the description of kinetics.', year=2016, embedding=None)
```

The code goes to great efforts to avoid duplicate author entries, using singletons and relying on ORCID when available.

Some more examples can be found as Jupyter notebooks in the `examples` directory.

## Installation

You need the [poetry](https://python-poetry.org) package manager to install `my-scientific-profile`. You can then simply add the package using the command:
```bash
poetry add git+ssh://git@lin0.thphys.uni-heidelberg.de:bereau/my_scientific_profile.git#master
```
followed by `poetry install`. `poetry shell` will activate a local environment, in which `my-scientific-profile` will be available.

## Configuration

Copy the file `my_scientific_profile/config_default.yaml` into your local config directory, e.g. `~/.config/my_scientific_profile/config.yaml`. There are several fields:

- my-orcid: is your ORCID
- s3-bucket: optional, if you want to store the data on AWS S3
- email-address: for the Unpaywall API
- authors: you can provide the ORCID of some of your collaborators. This may help resolve some difficulties when searching by name. Leave blank (i.e., '[]') to leave empty.
- papers: abstracts are sometimes difficult to retrieve. You can add them there, accompanied by the corresponding DOI, as a fallback.

## Misc

* Free software: MIT license
* Documentation: None (living on the edge).
* Tests: None (definitely living on the edge).

## Credits

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

- Cookiecutter: https://github.com/audreyr/cookiecutter
- `audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
