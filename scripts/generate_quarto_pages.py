import os
from pathlib import Path

from my_scientific_profile.authors.authors import search_author_from_config_info
from my_scientific_profile.config.config import get_authors_with_categories
from my_scientific_profile.database.authors import load_all_paper_authors_from_s3
from my_scientific_profile.database.papers import load_all_papers_from_s3
from my_scientific_profile.utils.utils import ROOT_DIR
from my_scientific_profile.database.aws_s3 import S3_BUCKET, S3_CLIENT
from my_scientific_profile.quarto.authors import save_quarto_author_page_to_file
from my_scientific_profile.quarto.papers import save_quarto_paper_page_to_file

path = Path(ROOT_DIR).parent
team_path = path.joinpath("quarto_website").joinpath("group")
existing_files = os.listdir(team_path)

for file_name in existing_files:
    if file_name.endswith(".qmd"):
        os.remove(os.path.join(team_path, file_name))

authors = load_all_paper_authors_from_s3(s3_client=S3_CLIENT, s3_bucket=S3_BUCKET)

author_infos_with_categories = get_authors_with_categories()
authors_with_categories = []
for author_info in author_infos_with_categories:
    authors_with_categories.append(search_author_from_config_info(author_info))
for author in authors_with_categories:
    save_quarto_author_page_to_file(
        author, str(team_path.joinpath(f"{author.lower_case_snake_name}.qmd"))
    )


papers = load_all_papers_from_s3(s3_client=S3_CLIENT, s3_bucket=S3_BUCKET)
paper_path = path.joinpath("quarto_website").joinpath("papers")
existing_files = os.listdir(paper_path)

for file_name in existing_files:
    if file_name.endswith(".qmd"):
        os.remove(os.path.join(paper_path, file_name))

for i, paper in enumerate(reversed(papers)):
    save_quarto_paper_page_to_file(
        paper, str(paper_path.joinpath(f"paper_{i:03d}.qmd"))
    )
