import traceback
import logging
import os
import json
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
import util
import models

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DB_HOST']
db = SQLAlchemy(app)

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
		app.logger.info(models.StarLog.query.all()[0].getJson())
		return 'ok'
	elif request.method == 'POST':
		try:
			posted = models.StarLog(request.data)
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
			return probe.probeStarLog(jsonData), 200
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
	
	@app.route('/debug/unpack-hex-difficulty', methods=['POST'])
	def routDebugUnpackHexDifficulty():
		try:
			jsonData = request.get_json()
			return util.unpackBits(util.difficultyFromHex(jsonData['hex_difficulty'])), 200
		except:
			traceback.print_exc()
			return '400', 400

if __name__ == '__main__':
	if 0 < util.difficultyFudge:
		app.logger.info('All hash difficulty will be calculated with DIFFICULTY_FUDGE %s' % (util.difficultyFudge))
	app.run()
