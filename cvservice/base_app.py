import os
from json import load as load_json
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from cvservice.controllers.block_controller import BlockController
from cvservice.controllers.rules_controller import RulesController
from cvservice.models.event_model_type import EventModelType
from cvservice.models.event_type import EventType
from cvservice.models.event_usage import EventUsage
from cvservice.rules import Rules

class BaseApp():

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
        self.rules_controller = RulesController(self)

        self.flask_app.run(use_reloader=False)


    def initialize_database(self):
        self.database = SQLAlchemy()

        self.database.app = self.flask_app
        self.database.init_app(self.flask_app)
        self.database.create_all()

        self.populate_types(EventModelType, Rules.EVENT_MODEL_TYPES)
        self.populate_types(EventType, Rules.EVENT_TYPES)
        self.populate_types(EventUsage, Rules.EVENT_USAGES)


    def populate_types(self, type_class, type_names):
        session = self.database.session()
        try:
            for existing in session.query(type_class).all():
                if existing.name not in type_names:
                    raise Exception('Database already contains unrecognized value %s' % existing.name)
                type_names.remove(existing.name)
            for current_type in type_names:
                if current_type == 'unknown':
                    continue
                session.add(type_class(current_type))
            session.commit()
        finally:
            session.close()