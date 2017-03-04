import traceback
import logging
import os
import json
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DB_HOST']
db = SQLAlchemy(app)

import util
from models import StarLog

starLogsMaxLimit = int(os.getenv('STARLOG_MAX_LIMIT', 10))
# TODO: Should there be a max offset?

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

@app.route('/star-logs', methods=['GET', 'POST'])
def routeStarLogs():
	if request.method == 'GET':
		try:
			previousHash = request.args.get('previous_hash')
			beforeTime = request.args.get('before_time')
			sinceTime = request.args.get('since_time')
			limit = request.args.get('limit')
			offset = request.args.get('offset')
			query = StarLog.query
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
			posted = StarLog(request.data, db.session)
			db.session.add(posted)
			db.session.commit()
		except:
			traceback.print_exc()
			return '400', 400
		return '200', 200

# TODO: Move this somewhere?
if app.debug:
	import probe

	@app.route('/debug/hash-star-log', methods=['POST'])
	def routeDebugHashStarLog():
		try:
			jsonData = request.get_json()
			return json.dumps(util.hashStarLog(jsonData)), 200
		except:
			traceback.print_exc()
			return '400', 400

	@app.route('/debug/probe-star-log', methods=['POST'])
	def routeDebugProbeStarLog():
		try:
			jsonData = request.get_json()
			result = probe.probeStarLog(jsonData)
			return json.dumps(result[1]) , 200
		except:
			traceback.print_exc()
			return '400', 400

	@app.route('/debug/sign-jump', methods=['POST'])
	def routeDebugSignJump():
		try:
			jsonData = request.get_json()
			signature = util.signHash(str(jsonData['private_key']), util.concatJump(jsonData))
			return json.dumps({
				'private_key': jsonData['private_key'],
				'public_key': jsonData['public_key'],
				'fleet': jsonData['fleet'],
				'key': jsonData['key'],
				'origin': jsonData['origin'],
				'destination': jsonData['destination'],
				'count': jsonData['count'],
				'signature': signature
			}), 200
		except:
			traceback.print_exc()
			return '400', 400

	@app.route('/debug/verify-jump', methods=['POST'])
	def routeDebugVerifyJump():
		try:
			jsonData = request.get_json()
			return 'valid' if util.verifyJump(jsonData) else 'invalid'
		except:
			traceback.print_exc()
			return '400', 400
	
	@app.route('/debug/unpack-difficulty', methods=['POST'])
	def routeDebugUnpackDifficulty():
		try:
			jsonData = request.get_json()
			return util.unpackBits(jsonData['difficulty']), 200
		except:
			traceback.print_exc()
			return '400', 400

	@app.route('/debug/unpack-hex-difficulty', methods=['POST'])
	def routeDebugUnpackHexDifficulty():
		try:
			jsonData = request.get_json()
			return util.unpackBits(util.difficultyFromHex(jsonData['hex_difficulty'])), 200
		except:
			traceback.print_exc()
			return '400', 400
	
	@app.route('/debug/difficulty-change', methods=['POST'])
	def routeDebugDifficultyChange():
		try:
			jsonData = request.get_json()
			return str(util.calculateDifficulty(jsonData['difficulty'], jsonData['duration'])), 200
		except:
			traceback.print_exc()
			return '400', 400

if __name__ == '__main__':
	if 0 < util.difficultyFudge:
		app.logger.info('All hash difficulty will be calculated with DIFFICULTY_FUDGE %s' % (util.difficultyFudge))
	app.run()
