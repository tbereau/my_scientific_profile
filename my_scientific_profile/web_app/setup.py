import logging
import os

from decouple import config as environ
from flask import Flask, render_template, request

from my_scientific_profile.database.papers import load_all_papers_from_s3
from my_scientific_profile.search.search import get_search_index
from my_scientific_profile.web_app.extensions import S3_BUCKET, s3, s3_client
from my_scientific_profile.web_app.forms import SearchForm

logger = logging.getLogger(__name__)


PAPERS = load_all_papers_from_s3(s3_client, S3_BUCKET)


def create_app(test_config=None):
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

    with app.app_context():
        s3.init_app(app)

    @app.route("/papers")
    def all_papers():
        return render_template("papers.html", papers=PAPERS)

    @app.route("/papers/<doi>")
    def individual_paper(doi: str):
        paper = next(paper for paper in PAPERS if paper.doi == (doi.replace("_", "/")))
        logger.info(paper)
        return render_template("paper.html", paper=paper)

    @app.route("/search-papers", methods=["GET", "POST"])
    def search_papers():
        if request.method == "POST":
            result = dict(request.form)
            logger.info(f"result {dict(result)}")
            search_index = get_search_index()
            results = search_index.search(result["search"])
            logger.info(f"search results {results}")
            dois = [entry["ref"] for entry in results]
            papers = [paper for paper in PAPERS if paper.doi in dois]
            return render_template("papers.html", papers=papers)

    @app.route("/")
    def index():
        form = SearchForm()
        return render_template("index.html", form=form)

    @app.context_processor
    def inject_static_url():
        static_url = f"https://{app.config['FLASKS3_BUCKET_NAME']}.s3.amazonaws.com/"
        return dict(static_url=static_url)

    return app
