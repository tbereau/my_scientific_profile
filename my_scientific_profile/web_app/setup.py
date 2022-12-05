import logging
import os

from decouple import config as environ
from flask import Flask, render_template, request

from my_scientific_profile.database.papers import load_all_papers_from_s3
from my_scientific_profile.search.search import get_search_index
from my_scientific_profile.web_app.extensions import S3_BUCKET, s3, s3_client

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

    search_index = get_search_index()

    with app.app_context():
        s3.init_app(app)

    @app.route("/papers")
    def papers_all():
        return render_template("papers.html", papers=PAPERS)

    @app.route("/papers/<dois>")
    def papers(dois):
        logger.info(f"papers dois {dois}")
        _dois = [doi.replace("_", "/") for doi in dois.split(",")]
        logger.info(f"dois {_dois}")
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
        logger.info(paper)
        return render_template("paper.html", paper=paper)

    @app.route("/search", methods=["POST"])
    def search():
        logger.info(f"requests {request.args}")
        logger.info(f"form {request.form}")
        result = dict(request.form)
        try:
            results = search_index.search(result["search"])
        except KeyError:
            return {}
        logger.info(f"search results {len(results)}")
        dois = [entry["ref"] for entry in results]
        dois = ",".join([doi.replace("/", "_") for doi in dois])
        logger.info(f"search dois {dois}")
        return dois

    @app.route("/", methods=["GET"], defaults={"dois": [p.doi for p in PAPERS][:5]})
    @app.route("/<dois>", methods=["GET"])
    def index(dois: str):
        _dois = ",".join([doi.replace("/", "_") for doi in dois])
        logger.info(f"index.html {_dois}")
        return render_template("index.html", dois=_dois)

    @app.context_processor
    def inject_static_url():
        static_url = f"https://{app.config['FLASKS3_BUCKET_NAME']}.s3.amazonaws.com/"
        return dict(static_url=static_url)

    return app
