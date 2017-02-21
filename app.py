from __future__ import print_function
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
import sys, traceback
import os
import cryptography
import hashlib
import json

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
		return "ok"
	elif request.method == "POST":
		try:
			posted = models.StarLog.initFromDictionary(request.get_json()[0])
		except:
			traceback.print_exc(file=sys.stderr)
			return "400", 400
		return "200", 200

import models

if __name__ == "__main__":
	app.run(debug=isDebug)
