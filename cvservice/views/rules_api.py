from flask import request

class RulesApi():

    def __init__(self, rules_controller):
        self.rules_controller = rules_controller

    def get(self):
        return self.rules_controller.get()