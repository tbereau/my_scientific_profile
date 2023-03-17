import json
import logging
import os
from dataclasses import asdict

import pandas as pd
import plotly.graph_objects as go
from bokeh.embed import json_item
from bokeh.models import Legend
from bokeh.plotting import figure
from bokeh.transform import linear_cmap
from decouple import config as environ
from flask import Flask, render_template, request
from plotly.utils import PlotlyJSONEncoder

from my_scientific_profile.database.papers import load_all_papers_from_s3
from my_scientific_profile.search.search import get_search_index
from my_scientific_profile.web_app.extensions import S3_BUCKET, s3, s3_client

logger = logging.getLogger(__name__)

PAPERS = load_all_papers_from_s3(s3_client, S3_BUCKET)
MAPBOX_TOKEN = environ("MAPBOX_TOKEN")


def create_app(test_config=None):  # noqa
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY="dev",
        DATABASE=os.path.join(app.instance_path, "flaskr.sqlite"),
    )
    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    app.config["AWS_ACCESS_KEY_ID"] = environ("AWS_ACCESS_KEY_ID")
    app.config["AWS_SECRET_ACCESS_KEY"] = environ("AWS_SECRET_ACCESS_KEY")
    app.config["AWS_DEFAULT_REGION"] = environ("AWS_DEFAULT_REGION")
    app.config["FLASKS3_BUCKET_NAME"] = environ("AWS_STORAGE_BUCKET_NAME")

    search_index = get_search_index()

    with app.app_context():
        s3.init_app(app)

    df_b = pd.json_normalize([asdict(p) for p in PAPERS], sep="_")  # noqa
    topics = {p.embedding.topic_number: p.embedding.topic_name for p in PAPERS}

    @app.route("/papers")
    def papers_all():
        return render_template("papers.html", papers=PAPERS)

    @app.route("/papers/<dois>")
    def papers(dois):
        logger.debug(f"papers dois {dois}")
        _dois = [doi.replace("_", "/") for doi in dois.split(",")]
        logger.debug(f"dois {_dois}")
        _papers = [paper for paper in PAPERS if paper.doi in _dois]
        return render_template("papers.html", papers=_papers)

    @app.route("/paper/<doi>")
    def individual_paper(doi: str):
        try:
            paper = next(
                paper for paper in PAPERS if paper.doi == (doi.replace("_", "/"))
            )
        except StopIteration:
            return f"cannot find DOI {doi.replace('_', '/')}"
        logger.debug(paper)
        return render_template("paper.html", paper=paper)

    @app.route("/search", methods=["POST"])
    def search():
        logger.debug(f"requests {request.args}")
        logger.debug(f"form {request.form}")
        result = dict(request.form)
        try:
            results = search_index.search(result["search"])
        except KeyError:
            return {}
        logger.debug(f"search results {len(results)}")
        dois = [entry["ref"] for entry in results]
        dois = ",".join([doi.replace("/", "_") for doi in dois])
        logger.debug(f"search dois {dois}")
        return dois

    @app.route("/", methods=["GET"], defaults={"dois": [p.doi for p in PAPERS][:]})
    @app.route("/<dois>", methods=["GET"])
    def index(dois: str):
        _dois = ",".join([doi.replace("/", "_") for doi in dois])
        logger.debug(f"index.html {_dois}")
        return render_template("index.html", dois=_dois, topics=topics)

    @app.route("/topic/<topic_number>")
    def filter_topic(topic_number: int):
        topic_number = int(topic_number)
        logger.info(f"topic number {topic_number}")
        _dois = [p.doi for p in PAPERS if p.embedding.topic_number == topic_number]
        return index(_dois)

    @app.route("/lit-graph-data")
    def literature_graph_data():
        logger.debug("literature graph")
        fig = figure(
            height=800,
            title="Literature graph",
            x_axis_location=None,
            y_axis_location=None,
            tooltips=[
                ("Topic", "@embedding_topic_name"),
                ("Title", "@title"),
                ("Ref", "@journal_name (@year)"),
                ("DOI", "@doi"),
            ],
        )
        fig.add_layout(Legend(), "below")
        fig.sizing_mode = "stretch_width"
        fig.scatter(
            x="embedding_x",
            y="embedding_y",
            source=df_b,
            size=20,
            alpha=0.7,
            line_width=0,
            legend_field="embedding_topic_name",
            fill_color=linear_cmap(
                "embedding_topic_number",
                "Turbo256",
                0,
                df_b["embedding_topic_number"].max(),
            ),
        )
        return json.dumps(json_item(fig, "lit_graph"))

    @app.route("/lit-graph")
    def literature_graph():
        return render_template("lit_graph.html")

    @app.route("/contact")
    def contact():
        graph_json = get_map()
        return render_template("contact.html", graphJSON=graph_json)

    def get_map():
        fig = go.Figure(
            go.Scattermapbox(
                lat=["49.414990"],
                lon=["8.698440"],
                mode="markers",
                marker=go.scattermapbox.Marker(size=14),
                text=["Institute for Theoretical Physics"],
            )
        )

        fig.update_layout(
            hovermode="closest",
            mapbox=dict(
                accesstoken=MAPBOX_TOKEN,
                bearing=0,
                center=go.layout.mapbox.Center(lat=49.414, lon=8.698),
                pitch=0,
                zoom=12,
            ),
        )
        return json.dumps(fig, cls=PlotlyJSONEncoder)

    @app.context_processor
    def inject_static_url():
        static_url = f"https://{app.config['FLASKS3_BUCKET_NAME']}.s3.amazonaws.com/"
        return dict(static_url=static_url)

    return app
