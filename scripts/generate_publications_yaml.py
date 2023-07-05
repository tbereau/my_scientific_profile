from my_scientific_profile.database.papers import load_all_papers_from_s3
from my_scientific_profile.database.aws_s3 import S3_BUCKET, s3_client

papers = load_all_papers_from_s3(s3_client=s3_client, s3_bucket=S3_BUCKET)

for paper in papers:
    print(paper.to_yaml())
