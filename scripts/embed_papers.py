import nltk
import numpy as np
import pandas as pd

nltk.download("stopwords")
nltk.download("omw-1.4")
nltk.download("wordnet")
wn = nltk.WordNetLemmatizer()
from dataclasses import asdict  # noqa

from bertopic import BERTopic  # noqa
from sentence_transformers import SentenceTransformer  # noqa
from umap import UMAP  # noqa

from my_scientific_profile.database.papers import (  # noqa
    load_all_papers_from_s3,
    save_all_papers_to_s3,
)
from my_scientific_profile.papers.papers import Embedding  # noqa
from my_scientific_profile.database.aws_s3 import S3_BUCKET, S3_CLIENT  # noqa

papers = load_all_papers_from_s3(s3_client=S3_CLIENT, s3_bucket=S3_BUCKET)
df = pd.json_normalize(list(asdict(p) for p in papers))  # noqa
stopwords = nltk.corpus.stopwords.words("english")
df["abstract"] = df["abstract"].fillna("")
df["abstract_without_stopwords"] = df["abstract"].apply(
    lambda x: " ".join([w for w in x.split() if w.lower() not in stopwords])
)
df["abstract_lemmatized"] = df["abstract_without_stopwords"].apply(
    lambda x: " ".join([wn.lemmatize(w) for w in x.split() if w not in stopwords])
)
umap_model = UMAP(
    n_neighbors=2, n_components=2, min_dist=0.0, metric="euclidean", random_state=100
)
topic_model = BERTopic(
    umap_model=umap_model,
    min_topic_size=2,
    top_n_words=10,
).fit(df["abstract_lemmatized"])
sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = sentence_model.encode(df["abstract_lemmatized"])

topic_labels = topic_model.generate_topic_labels(
    nr_words=3, topic_prefix=False, word_length=15, separator=" | "
)
topic_model.set_topic_labels(topic_labels)
df["topic"] = topic_model.topics_
plotly_obj = topic_model.visualize_documents(
    docs=df.index,
    embeddings=embeddings,
    hide_annotations=False,
    custom_labels=True,
    title="Literature graph",
)
df_coord = pd.json_normalize(
    [
        {"paper_id": int(index), "x": x, "y": y}
        for d in plotly_obj.data
        for index, x, y in zip(d["hovertext"], d["x"], d["y"])
        if not np.isnan(index)
    ]
)
df_coord["topic"] = df.iloc[df_coord["paper_id"].values].topic.values
topic_keys = list(topic_model.get_topics().keys())
df_coord["topic_name"] = df_coord.apply(lambda x: topic_labels[topic_keys.index(x["topic"])], axis=1)
df_coord["title"] = df_coord.apply(
    lambda x: f"{df.iloc[x['paper_id']].title[:50] + '...'}"
    if len(df.iloc[x["paper_id"]].title) > 50
    else df.iloc[x["paper_id"]].title,
    axis=1,
)
df_coord["doi"] = df.iloc[df_coord["paper_id"]].doi.values
for _, item in df_coord.iterrows():
    paper = [p for p in papers if p.doi == item["doi"]][0]
    paper.embedding = Embedding(
        x=item["x"],
        y=item["y"],
        topic_number=item["topic"],
        topic_name=item["topic_name"],
    )

save_all_papers_to_s3(S3_CLIENT, S3_BUCKET)
