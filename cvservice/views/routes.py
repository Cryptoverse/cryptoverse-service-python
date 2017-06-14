# import json
# from flask import Blueprint, request
# from cvservice import util

# api = Blueprint('api', __name__)

# @api.route('/')
# def route_index():
#     return 'Running'


# @api.route("/rules")
# def get_rules():
#     return json.dumps({
#         'difficulty_fudge': util.difficultyFudge(),
#         'difficulty_duration': util.difficultyDuration(),
#         'difficulty_interval': util.difficultyInterval(),
#         'difficulty_start': util.difficultyStart(),
#         'ship_reward': util.shipReward(),
#         'cartesian_digits': util.cartesianDigits(),
#         'jump_cost_min': util.jumpCostMinimum(),
#         'jump_cost_max': util.jumpCostMaximum(),
#         'jump_distance_max': util.jumpDistanceMaximum(),
#         'star_logs_max_limit': util.starLogsMaxLimit(),
#         'events_max_limit': util.eventsMaxLimit(),
#         'chains_max_limit': util.chainsMaxLimit()
#     })

# @api.route('/blocks')
# def get_blocks():
#     previous_hash = request.args.get('previous_hash', None, type=str)
#     before_time = request.args.get('before_time', None, type=int)
#     since_time = request.args.get('since_time', None, type=int)
#     limit = request.args.get('limit', 1, type=int)
#     offset = request.args.get('offset', None, type=int)

#     return app.block_controller.get_starlogs(previous_hash, before_time,
#                                              since_time, limit, offset)

#     return results


# @api.route('/star-logs', methods=['POST'])
# def post_star_logs():
#     result = StarLogController.add_starlog(request.data)
#     if result:
#         return "200", 200
#     else:
#         return "400", 400


# @api.route('/events')
# def get_events():
#     limit = request.args.get('limit', 1, type=int)
#     results = EventController.get_events(limit)
#     return json.dumps(results)


# @api.route('/events', methods=['POST'])
# def post_events():
#     EventController.add_events(request.data)