from my_scientific_profile.authors.authors import Author
from my_scientific_profile.config.config import find_author_in_config


def generate_quarto_author_page(author: Author) -> str:
    author_info = find_author_in_config(author.given, author.family)
    icon_links = get_icon_links_for_author(author_info)
    image = f"../static/{author_info.get('image') or 'cgmol.jpg'}"
    categories = (
        author_info.get("categories")
        and "categories:\n"  # noqa
        + "\n".join(["  - " + cat for cat in author_info.get("categories")])  # noqa
        or ""  # noqa
    )
    header = f"""
---
title: "{author.full_name}"
format:
  html:
    echo: false
    keep-hidden: true
{categories}
image: {image}
about:
  id: hero-heading
  template: solana
  image: {image}
{icon_links}
---
"""
    summary = author_info.get("summary") or ""
    experience = (
        author_info.get("experience")
        and "## Experience\n\n"  # noqa
        + "\n\n".join([item for item in author_info.get("experience")])  # noqa
        or ""  # noqa
    )
    education = (
        author_info.get("education")
        and "## Education\n\n"  # noqa
        + "\n\n".join([item for item in author_info.get("education")])  # noqa
        or ""  # noqa
    )
    body = f"""

:::{{#hero-heading}}

{summary}

{experience}

{education}
:::


```{{ojs}}
import {{Plot}} from "@mkfreeman/plot-tooltip"
import {{map}} from "@martien/ramda"

papers_r = FileAttachment("../data/all_papers.json").json()
n_columns = Object.entries(papers_r["doi"]).length
index_array = Array.from({{length: n_columns}}, (_, i) => i)
papers = map(i => map(x => x[i], papers_r), index_array)

my_papers = papers.filter(function(p) {{
    return p.authors.map(a => a.full_name).includes("{author.full_name}")
}})

Inputs.table(my_papers, {{
    columns: [
    "doi",
    "title",
    "journal.name",
    "journal.volume",
    "journal.issue",
    "journal.pages",
    "year",
    "embedding.topic_name"
  ],
  format: {{
    doi: doi => htl.html`<a href=https://doi.org/${{doi}} target=_blank>${{doi}}</a>`
  }},
  width: {{
    "title": 10
  }},
  layout: "fixed",
}})
```
"""
    return header + body


def get_icon_links_for_author(author_info: dict) -> str:
    field_map = {
        "twitter": {"icon": "twitter", "text": "twitter"},
        "github": {"icon": "github", "text": "Github"},
        "website": {"icon": "house", "text": "Website"},
        "scholar": {"icon": "google", "text": "Google Scholar"},
    }

    def get_author_links(author_info_: dict, field: str) -> str:
        if href := author_info_.get(field):
            return f"""
    - icon: {field_map[field]["icon"]}
      text: {field_map[field]["text"]}
      href: {href}"""
        return ""

    icon_links = "".join(
        [get_author_links(author_info, field) for field in list(field_map.keys())]
    )
    if icon_links != "":
        icon_links = f"""  links:
{icon_links}"""
    return icon_links
