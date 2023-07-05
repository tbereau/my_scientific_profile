from my_scientific_profile.papers.papers import (
    fetch_all_paper_authors,
    fetch_all_paper_infos,
)

papers = fetch_all_paper_infos()
paper_authors = fetch_all_paper_authors()
print(f"fetched {len(papers)} papers and {len(paper_authors)} authors")

from my_scientific_profile.database.authors import save_all_paper_authors_to_s3  # noqa
from my_scientific_profile.database.papers import save_all_papers_to_s3  # noqa
from my_scientific_profile.database.aws_s3 import S3_BUCKET, S3_CLIENT  # noqa

save_all_papers_to_s3(s3_client=S3_CLIENT, s3_bucket=S3_BUCKET)
save_all_paper_authors_to_s3(s3_client=S3_CLIENT, s3_bucket=S3_BUCKET)
print(f"saved to S3 {S3_CLIENT}")
