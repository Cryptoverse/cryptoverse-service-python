import traceback
import logging
import os
import json
from flask import Flask, request

# TODO: Do these still need to be separated from the rest of the imports?
import util
import validate
import verify
from models import database, initialize_models, StarLog, Fleet, Chain, \
    ChainIndex, Event, EventSignature, EventInput, EventOutput, \
    StarLogEventSignature
import factory
from controllers import EventController, ChainController, StarLogController

app = factory.create_app({})
app.debug = 0 < os.getenv('CV_DEBUG', 0)
app.config['SQLALCHEMY_DATABASE_URI'] = \
    os.getenv('DB_HOST', 'sqlite:///service.db')

database.app = app
database.init_app(app)
database.create_all()


@app.before_first_request
def setup_logging():
    if not app.debug:
        # In production mode, add log handler to sys.stderr.
        app.logger.addHandler(logging.StreamHandler())
        app.logger.setLevel(logging.INFO)


@app.route('/')
def route_index():
    return 'Running'


def test_route_index():
    assert route_index() == 'Running'


@app.route("/rules")
def get_rules():
    return json.dumps({
        'difficulty_fudge': util.difficultyFudge(),
        'difficulty_duration': util.difficultyDuration(),
        'difficulty_interval': util.difficultyInterval(),
        'difficulty_start': util.difficultyStart(),
        'ship_reward': util.shipReward(),
        'cartesian_digits': util.cartesianDigits(),
        'jump_cost_min': util.jumpCostMinimum(),
        'jump_cost_max': util.jumpCostMaximum(),
        'jump_distance_max': util.jumpDistanceMaximum(),
        'star_logs_max_limit': util.starLogsMaxLimit(),
        'events_max_limit': util.eventsMaxLimit(),
        'chains_max_limit': util.chainsMaxLimit()
    })


@app.route('/chains')
def get_chains():
    height = request.args.get('height', None, type=int)
    limit = request.args.get('limit', 1, type=int)
    results = ChainController.get_chains(limit, height)
    return json.dumps(results)


@app.route('/star-logs')
def get_star_logs():
    previous_hash = request.args.get('previous_hash', None, type=str)
    before_time = request.args.get('before_time', None, type=int)
    since_time = request.args.get('since_time', None, type=int)
    limit = request.args.get('limit', 1, type=int)
    offset = request.args.get('offset', None, type=int)

    results = StarLogController.get_starlogs(previous_hash, before_time,
                                             since_time, limit, offset)

    return results


@app.route('/star-logs', methods=['POST'])
def post_star_logs():
    result = StarLogController.add_starlog(request.data)
    if result:
        return "200", 200
    else:
        return "400", 400


@app.route('/events')
def get_events():
    limit = request.args.get('limit', 1, type=int)
    results = EventController.get_events(limit)
    return json.dumps(results)


@app.route('/events', methods=['POST'])
def post_events():
    EventController.add_events(request.data)

if __name__ == '__main__':
    if 0 < util.difficultyFudge():
        app.logger.info('All hash difficulties will be calculated with DIFFICULTY_FUDGE %s' % (util.difficultyFudge()))
    initialize_models()
    app.run(use_reloader=False)
