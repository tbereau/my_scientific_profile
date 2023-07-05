# My Scientific Profile

Programmatically retrieve information about your scientific publications from APIs. The code is strongly based on ORCID as well as CrossRef. For best results, make sure that most of your publications are listed there. APIs supported:

- ORCID
- CrossRef
- doi2bib (for bibtex reference)
- Semantic Scholar (for tldr, among others)
- Unpaywall (for preprint info)

The library generates `Paper` and `Author` objects that contain various information about a scientific publication and author, respectively.

This library is used to automatically generate all publication and collaborator information on my [personal website](https://tristanbereau.com) and [CV](https://tristanbereau.com/files/bereau_cv.pdf).

## Highlight

A paper can be queried simply by its DOI:
```python
from my_scientific_profile.papers.papers import fetch_paper_info
paper1 = fetch_paper_info("10.1140/epjst/e2016-60114-5")
```

Here's the content of `paper1`:

```python
Paper(doi='10.1140/epjst/e2016-60114-5', title='Concurrent parametrization against static and kinetic information leads to more robust coarse-grained force fields', journal=JournalInfo(name='The European Physical Journal Special Topics', url='http://dx.doi.org/10.1140/epjst/e2016-60114-5', issue='8-9', abbreviation='Eur. Phys. J. Spec. Top.', pages='1373-1389', volume=225), publication_date=datetime.datetime(2016, 7, 15, 7, 35, 24, tzinfo=TzInfo(UTC)), authors=[Author(given='J.F.', family='Rudzinski', affiliation=Affiliation(name=None, city=None, country=None), orcid=None, email=None, full_name='J.F. Rudzinski', uuid='bdc74bb4-1b51-11ee-b8f8-a2a06772f9f1'), Author(given='T.', family='Bereau', affiliation=Affiliation(name=None, city=None, country=None), orcid=None, email=None, full_name='T. Bereau', uuid='be2ca9be-1b51-11ee-b8f8-a2a06772f9f1')], citation_count=17, open_access=OpenAccessPaperInfo(is_open_access=True, open_access_status='green', landing_page_url='http://arxiv.org/abs/1607.05492', pdf_url='http://arxiv.org/pdf/1607.05492'), bib_entry='@article{Rudzinski_2016,\n\tdoi = {10.1140/epjst/e2016-60114-5},\n\turl = {https://doi.org/10.1140%2Fepjst%2Fe2016-60114-5},\n\tyear = 2016,\n\tmonth = {jul},\n\tpublisher = {Springer Science and Business Media {LLC}},\n\tvolume = {225},\n\tnumber = {8-9},\n\tpages = {1373--1389},\n\tauthor = {J.F. Rudzinski and T. Bereau},\n\ttitle = {Concurrent parametrization against static and kinetic information leads to more robust coarse-grained force fields},\n\tjournal = {The European Physical Journal Special Topics}\n}', abstract='The parametrization of coarse-grained (CG) simulation models for molecular systems often aims at reproducing static properties alone. The reduced molecular friction of the CG representation usually results in faster, albeit inconsistent, dynamics. In this work, we rely on Markov state models to simultaneously characterize the static and kinetic properties of two CG peptide force fields—one top-down and one bottom-up. Instead of a rigorous evolution of CG dynamics (e.g., using a generalized Langevin equation), we attempt to improve the description of kinetics by simply altering the existing CG models, which employ standard Langevin dynamics. By varying masses and relevant force-field parameters, we can improve the timescale separation of the slow kinetic processes, achieve a more consistent ratio of mean-first-passage times between metastable states, and refine the relative free-energies between these states. Importantly, we show that the incorporation of kinetic information into a structure-based parametrization improves the description of the helix-coil transition sampled by a minimal CG model. While structure-based models understabilize the helical state, kinetic constraints help identify CG models that improve the ratio of forward/backward timescales by effectively hindering the sampling of spurious conformational intermediate states.', tldr='This work relies on Markov state models to simultaneously characterize the static and kinetic properties of two CG peptide force fields—one top-down and one bottom-up—in order to improve the description of kinetics.', year=2016, embedding=None)
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
