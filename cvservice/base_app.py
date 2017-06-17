from os import getenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from cvservice.controllers.block_controller import BlockController
from cvservice.models.event_model_type import EventModelType
from cvservice.models.event_type import EventType
from cvservice.models.event_usage import EventUsage
from cvservice.util import EVENT_MODEL_TYPES, EVENT_TYPES, EVENT_USAGES
from cvservice.views.block_api import BlockApi

class BaseApp():

    def __init__(self):
        self.flask_app = Flask(__name__)
        self.flask_app.debug = 0 < getenv('CV_DEBUG', 0)
        self.flask_app.config['SQLALCHEMY_DATABASE_URI'] = getenv('DB_HOST', 'sqlite:///service.db')
        
        self.initialize_database()

        self.block_controller = BlockController(self)

        self.flask_app.run(use_reloader=False)

    def initialize_database(self):
        self.database = SQLAlchemy()

        self.database.app = self.flask_app
        self.database.init_app(self.flask_app)
        self.database.create_all()

        self.populate_types(EventModelType, EVENT_MODEL_TYPES)
        self.populate_types(EventType, EVENT_TYPES)
        self.populate_types(EventUsage, EVENT_USAGES)

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