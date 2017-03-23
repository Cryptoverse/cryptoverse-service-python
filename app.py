import logging
import os
import json
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS, cross_origin

starLogsMaxLimit = int(os.getenv('STARLOG_MAX_LIMIT', '10'))
chainsMaxLimit = int(os.getenv('CHAINS_MAX_LIMIT', '10'))
isDebug = 0 < os.getenv('CV_DEBUG', 0)

app = Flask(__name__)
app.debug = isDebug
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DB_HOST']
database = SQLAlchemy(app)
CORS(app)

import util
import validate
from tasks import tasker
from models import StarLog

@app.before_first_request
def setupLogging():
	if not app.debug:
		# In production mode, add log handler to sys.stderr.
		app.logger.addHandler(logging.StreamHandler())
		app.logger.setLevel(logging.INFO)

@app.route('/')
def routeIndex():
	return 'Running'

@app.route("/rules")
def getRules():
	return json.dumps({
		'difficulty_fudge': util.difficultyFudge,
		'difficulty_duration': util.difficultyDuration,
		'difficulty_interval': util.difficultyInterval,
		'difficulty_start': util.difficultyStart,
		'ship_reward': util.shipReward
	})

@app.route("/jobprogress")
@cross_origin()
def poll_state():
	if 'job' in request.args:
		job_id = request.args['job']
	else:
		return 'No job id given.'

	job = tasker.AsyncResult(job_id)
	data = job.result or job.state
	# meta = json.dumps(job.info)
	if data is None:
		return "{}"
	return str(json.dumps(data))

@app.route('/chains')
def getChains():
	height = request.args.get('height', None, type=int)
	limit = request.args.get('limit', 1, type=int)
	query = database.session.query(StarLog)
	if height is None:
		query = query.order_by(StarLog.height.desc())
	else:
		if height < 0:
			raise ValueError('height is out of range')
		query = query.filter_by(height=height)
	if chainsMaxLimit < limit:
		raise ValueError('limit greater than maximum allowed')
	query = query.limit(limit)
	matches = query.all()
	result = []
	for match in matches:
		result.append(match.getJson(database.session))
	return json.dumps(result)

@app.route('/star-logs')
def getStarLogs():
	previousHash = request.args.get('previous_hash', None, type=str)
	beforeTime = request.args.get('before_time', None, type=int)
	sinceTime = request.args.get('since_time', None, type=int)
	limit = request.args.get('limit', 1, type=int)
	offset = request.args.get('offset', None, type=int)
	query = database.session.query(StarLog)
	if previousHash is not None:
		if not validate.fieldIsSha256(previousHash):
			raise ValueError('previous_hash is not a Sha256 hash')
		query = query.filter_by(previous_hash=previousHash)
	if beforeTime is not None:
		query = query.filter(StarLog.time < beforeTime)
	if sinceTime is not None:
		query = query.filter(sinceTime < StarLog.time)
	if sinceTime is not None and beforeTime is not None and beforeTime < sinceTime:
		raise ValueError('since_time is greater than before_time')
	if starLogsMaxLimit < limit:
		raise ValueError('limit greater than maximum allowed')
	if offset is not None:
		query = query.offset(offset)

	query = query.limit(limit)
	matches = query.all()
	result = []
	for match in matches:
		result.append(match.getJson(database.session))
	return json.dumps(result)

@app.route('/star-logs', methods=['POST'])
def postStarLogs():
	# TODO: Rollback if something goes wrong
	posted = StarLog(request.data, database.session)
	database.session.add(posted)
	database.session.commit()
	return '200', 200

@app.route('/jumps')
def getJumps():
	return 200

@app.route('/jumps', methods=['POST'])
def postJumps():
	return 200

if isDebug:
	from debug import debug
	app.register_blueprint(debug, url_prefix='/debug')

if __name__ == '__main__':
	if 0 < util.difficultyFudge:
		app.logger.info('All hash difficulties will be calculated with DIFFICULTY_FUDGE %s' % (util.difficultyFudge))
	app.run(use_reloader = False)
