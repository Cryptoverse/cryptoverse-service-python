from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
import cryptography
import hashlib

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/cryptoverse.db'
db = SQLAlchemy(app)

@app.route("/")
def routeIndex():
    if request.method == "GET":
        return "200"

@app.route("/star-logs", methods=["GET", "POST"])
def routeStarLogs():
    if request.method == "GET":
        print(models.StarLog.query.all()) #this is where
        return "ok"
    elif request.method == "POST":
        return "200", 200

import models

if __name__ == "__main__":
    app.run(debug=True)
