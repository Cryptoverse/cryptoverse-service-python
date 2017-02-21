from __future__ import print_function
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
import sys
import os
import cryptography
import hashlib

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ["DB_HOST"]
db = SQLAlchemy(app)

@app.route("/")
def routeIndex():
	if request.method == "GET":
		return "200"

@app.route("/star-logs", methods=["GET", "POST"])
def routeStarLogs():
	if request.method == "GET":
		print(models.StarLog.query.all(), file=sys.stderr)
		return "ok"
	elif request.method == "POST":
		return "200", 200

import models

if __name__ == "__main__":
	app.run(debug=os.environ["DEBUG"])
