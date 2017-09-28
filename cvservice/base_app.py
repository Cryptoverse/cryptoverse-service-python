import os
from json import load as load_json
from flask import Flask
from cvservice.models import Database
from cvservice.controllers.block_controller import BlockController
from cvservice.controllers.event_controller import EventController
from cvservice.controllers.rules_controller import RulesController
from cvservice.rules import Rules

class BaseApp(object):

    def __init__(self):
        self.flask_app = Flask(__name__)
        self.flask_app.debug = 0 < os.getenv('CV_DEBUG', 0)
        self.flask_app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DB_HOST', 'sqlite:///service.db')
        
        current_directory = os.path.dirname(__file__)
        config_path = os.path.join(current_directory, os.getenv('CONFIG_PATH', 'config.json'))
        with open(config_path) as config_file:
            config_json = load_json(config_file)
        
        self.rules = Rules(**config_json)

        self.initialize_database()

        self.block_controller = BlockController(self)
        self.event_controller = EventController(self)
        self.rules_controller = RulesController(self)

        self.flask_app.run(use_reloader=False)


    def initialize_database(self):
        self.database = Database

        self.database.app = self.flask_app
        self.database.init_app(self.flask_app)
        self.database.create_all()