from flask import Flask
import os


def create_app(extraArgs):
    app = Flask(__name__)

    for key, item in extraArgs.items():
        app.config[key] = item

    from models import database

    database.init_app(app)

    return app
