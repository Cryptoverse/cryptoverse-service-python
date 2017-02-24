from __future__ import print_function
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
import sys, traceback
import os
import cryptography
import hashlib
import json
import util

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ["DB_HOST"]
db = SQLAlchemy(app)
isDebug = os.environ["DEBUG"]

@app.route("/")
def routeIndex():
	if request.method == "GET":
		return "200"

@app.route("/star-logs", methods=["GET", "POST"])
def routeStarLogs():
	if request.method == "GET":
		print(models.StarLog.query.all()[0].getJson(), file=sys.stderr)
		return "ok"
	elif request.method == "POST":
		try:
			#print(request.data, file=sys.stderr)
			posted = models.StarLog.initFromJson(request.data)
			db.session.add(posted)
			db.session.commit()
		except:
			traceback.print_exc(file=sys.stderr)
			return "400", 400
		return "200", 200

# TODO: Move this somewhere?
if isDebug:
	@app.route("/debug/hash-star-log", methods=["POST"])
	def routeDebugHashStarLog():
		jsonData = request.get_json()
		try:
			return json.dumps(util.hashLog(jsonData)), 200
		except:
			traceback.print_exc(file=sys.stderr)
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
			traceback.print_exc(file=sys.stderr)
			return "400", 400

	@app.route("/debug/verify-jump", methods=["POST"])
	def routeDebugVerifyJump():
		jsonData = request.get_json()
		try:
			return 'valid' if util.verifyJump(jsonData) else 'invalid'
		except:
			traceback.print_exc(file=sys.stderr)
			return "400", 400

import models

if __name__ == "__main__":
	app.run(debug=isDebug)
