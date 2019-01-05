from flask import Flask
import os
from vocab.sentence_parser import render_jp


def create_app():
    """
    Used as Flask app factory.

    Creates and configures an instance of the Flask application.

    :return: Initialized flask app
    """
    app = Flask(__name__, instance_relative_config=True)
    app.secret_key = 'super secret key'
    app.config.from_object("vocab.config.Config")

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # register the database commands
    from vocab import db
    db.init_app(app)

    # apply the blueprints to the app
    from vocab import vocab
    app.register_blueprint(vocab.bp)
    app.add_url_rule('/', endpoint='index')
    app.jinja_env.globals.update(render_jp=render_jp)

    return app

