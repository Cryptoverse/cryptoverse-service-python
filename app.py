import traceback
import logging
import os
import json
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS, cross_origin

starLogsMaxLimit = int(os.getenv('STARLOG_MAX_LIMIT', 10))
isDebug = 0 < os.getenv('CV_DEBUG', 0)

app = Flask(__name__)
app.debug = isDebug
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DB_HOST']
database = SQLAlchemy(app)
CORS(app)

import util
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
	if request.method == 'GET':
		return '200'

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

@app.route('/star-logs', methods=['GET', 'POST'])
def routeStarLogs():
	if request.method == 'GET':
		try:
			previousHash = request.args.get('previous_hash')
			beforeTime = request.args.get('before_time')
			sinceTime = request.args.get('since_time')
			limit = request.args.get('limit')
			offset = request.args.get('offset')
			query = database.session.query(StarLog)
			if previousHash is not None:
				if not util.verifyFieldIsSha256(previousHash):
					raise ValueError('previous_hash is not a Sha256 hash')
				query = query.filter_by(previous_hash=previousHash)
			if beforeTime is not None:
				if not isinstance(beforeTime, int):
					raise TypeError('before_time is not an int')
				query = query.filter(StarLog.time < beforeTime)
			if sinceTime is not None:
				if not isinstance(sinceTime, int):
					raise TypeError('since_time is not an int')
				query = query.filter(sinceTime < StarLog.time)
			if sinceTime is not None and beforeTime is not None:
				if beforeTime < sinceTime:
					raise ValueError('since_time is greater than before_time')
			if limit is not None:
				if not isinstance(limit, int):
					raise TypeError('limit is not an int')
				if starLogsMaxLimit < limit:
					raise ValueError('limit greater than maximum allowed')
				query = query.limit(limit)
			else:
				query = query.limit(starLogsMaxLimit)
			if offset is not None:
				if not isinstance(offset, int):
					raise TypeError('offset is not an int')
				query = query.offset(offset)
			matches = query.all()
			result = []
			for match in matches:
				result.append(match.getJson())
			return json.dumps(result), 200
		except:
			traceback.print_exc()
			return '400', 400
	elif request.method == 'POST':
		try:
			posted = StarLog(request.data, database.session)
			database.session.add(posted)
			database.session.commit()
		except:
			traceback.print_exc()
			return '400', 400
		return '200', 200

if isDebug:
	from debug import debug
	app.register_blueprint(debug, url_prefix='/debug')

if __name__ == '__main__':
	if 0 < util.difficultyFudge:
		app.logger.info('All hash difficulty will be calculated with DIFFICULTY_FUDGE %s' % (util.difficultyFudge))
	app.run(use_reloader = False)
