import json
from cvservice.views.rules_api import RulesApi

class RulesController():

    def __init__(self, app):
        self.rules = app.rules
        self.database = app.database
        self.rules_api = RulesApi(self)

        app.flask_app.add_url_rule('/rules', 'get_rules', self.rules_api.get, methods=['GET'])

    def get(self):
        return json.dumps({
            'version': self.rules.version,
            'difficulty_fudge': self.rules.difficulty_fudge,
            'difficulty_duration': self.rules.difficulty_duration,
            'difficulty_interval': self.rules.difficulty_interval,
            'difficulty_start': self.rules.difficulty_start,
            'probe_reward': self.rules.probe_reward,
            'cartesian_digits': self.rules.cartesian_digits,
            'jump_cost_min': self.rules.jump_cost_min,
            'jump_cost_max': self.rules.jump_cost_max,
            'jump_distance_max': self.rules.jump_distance_max,
            'blocks_limit_max': self.rules.blocks_limit_max,
            'events_limit_max': self.rules.events_limit_max
        })