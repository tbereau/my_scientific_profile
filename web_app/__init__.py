import logging
import os

from flask import Flask, render_template

from my_scientific_profile.papers.papers import fetch_all_paper_infos, fetch_paper_info

logger = logging.getLogger(__name__)


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

    @app.route("/papers")
    def all_papers():
        papers = fetch_all_paper_infos().copy()
        logger.info(papers)
        return render_template("papers.html", papers=papers)

    @app.route("/papers/<doi>")
    def individual_paper(doi: str):
        paper = fetch_paper_info(doi.replace("-", "/"))
        logger.info(paper)
        return render_template("paper.html", paper=paper)

    return app
