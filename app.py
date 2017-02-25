from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
import logging
import sys, traceback
import os
import cryptography
import hashlib
import json
import util

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ["DB_HOST"]
db = SQLAlchemy(app)

@app.before_first_request
def setup_logging():
	if not app.debug:
		# In production mode, add log handler to sys.stderr.
		app.logger.addHandler(logging.StreamHandler())
        app.logger.setLevel(logging.INFO)
	

@app.route("/")
def routeIndex():
	if request.method == "GET":
		return "200"

@app.route("/star-logs", methods=["GET", "POST"])
def routeStarLogs():
	if request.method == "GET":
		app.logger.info(models.StarLog.query.all()[0].getJson())
		return "ok"
	elif request.method == "POST":
		try:
			posted = models.StarLog.initFromJson(request.data)
			db.session.add(posted)
			db.session.commit()
		except:
			traceback.print_exc()
			return "400", 400
		return "200", 200

# TODO: Move this somewhere?
if app.debug:
	@app.route("/debug/hash-star-log", methods=["POST"])
	def routeDebugHashStarLog():
		jsonData = request.get_json()
		try:
			return json.dumps(util.hashLog(jsonData)), 200
		except:
			traceback.print_exc()
			return "400", 400

	@app.route("/debug/sign-jump", methods=["POST"])
	def routeDebugSignJump():
		jsonData = request.get_json()
		try:
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
			return "400", 400

	@app.route("/debug/verify-jump", methods=["POST"])
	def routeDebugVerifyJump():
		jsonData = request.get_json()
		try:
			return 'valid' if util.verifyJump(jsonData) else 'invalid'
		except:
			traceback.print_exc()
			return "400", 400

import models

if __name__ == "__main__":
	app.run()
