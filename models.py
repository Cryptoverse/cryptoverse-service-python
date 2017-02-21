from app import db
from flask_sqlalchemy import SQLAlchemy
import hashlib
import cryptography
import json
import re
import util

class StarLog(db.Model):
    __tablename__ = "starlog"
    hash = db.Column(db.String(256), primary_key=True)
    height = db.Column(db.Integer)
    chain = db.Column(db.Integer)
    size = db.Column(db.Integer)
    log_header = db.Column(db.String(240))
    version = db.Column(db.Integer)
    previous_hash = db.Column(db.String(256))
    difficulty = db.Column(db.Integer)
    nonce = db.Column(db.Integer)
    time = db.Column(db.Integer)
    discovery_hash = db.Column(db.String(256))

    def __repr__(self):
        return '<StarLog %r>' % self.hash

    def __init__(
        hash,
        log_header,
        version,
        previous_hash,
        difficulty,
        nonce,
        time,
        state_hash,
        state
    ):
        if not isinstance(log_header, basestring):
            throw TypeError("Hash is not string")
        if not isinstance(log_header, basestring):
            throw TypeError("log_header is wrong type")
        if not isinstance(version, int):
            throw TypeError("version is not int")
        if not isinstance(log_header, basestring):
            throw TypeError("log_header is not string")
        if not isinstance(version, int):
            throw TypeError("version is not int")
        if not isinstance(previous_hash, basestring):
            throw TypeError("previous_hash is not string")
        if not isinstance(difficulty, int):
            throw TypeError("difficulty is not int")
        if not isinstance(nonce, int):
            throw TypeError("nonce is not int")
        if not isinstance(time, int):
            throw TypeError("time is not int")
        if not isinstance(state_hash, basestring):
            throw TypeError("state_hash is not string")
        if not isinstance(state, basestring):
            throw TypeError("state is not string")

        if not util.verifyFieldIsHash(hash):
            throw ValueError("hash is not a MD5 Hash")
        if not util.verifyFieldIsHash(previous_hash):
            throw ValueError("previous_hash is not a MD5 Hash")
        if not util.verifyFieldIsHash(state_hash):
            throw ValueError("state_hash is not a MD5 Hash")

        self.hash = hash
        self.log_header = log_header
        self.version = version
        self.previous_hash = previous_hash
        self.difficulty = difficulty
        self.nonce = nonce
        self.time = time
        self.state_hash = state_hash
        self.state = state

    def initFromJson(jsonData):
        obj = json.loads(jsonData)
        starlog = StarLog(
            obj['log_header'],
            obj['version'],
            obj['previous_hash'],
            obj['difficulty'],
            obj['nonce'],
            obj['time'],
            obj['state_hash'],
            obj['state'])

        return starlog

    def addFromJson(jsonData, parseJumpData=True, parseStarSystemData=True):
        sl = initFromJson(jsonData)
        db.session.add(sl)
        db.session.commit()

        jsonData = json.loads(jsonData)
        if 'jumps' in jsonData:
            for jump in jumps:


        if 'star_systems' in jsonData:
            pass



class StarSystem(db.Model):
    __tablename__ = "starsystem"
    starlog_id = db.Column(db.Integer(), primary_key=True)
    starlog = db.relationship('StarLog', backref=db.backref('starSystems', lazy='dynamic'))
    fleet = db.Column(db.String(256))

    def __repr__(self):
        return '<StarSystem %r>' % self.id


class Deployment(db.Model):
    __tablename__ = "deployment"
    id = db.Column(db.Integer, primary_key=True)
    starsystem_id = db.Column(db.Integer, db.ForeignKey('starsystem.id'))
    starsystem = db.relationship('StarSystem', backref=db.backref('deployments', lazy='dynamic'))
    fleet = db.Column(db.String(256))
    count = db.Column(db.Integer)

    def __repr__(self):
        return '<Deployment %r>' % self.id


class Jump(db.Model):
    __tablename__ = "jump"
    id = db.Column(db.Integer, primary_key=True)
    fleet = db.Column(db.String(256))
    jump_key = db.Column(db.String(256))
    origin_id = db.Column(db.Integer, db.ForeignKey('starsystem.id'))
    origin = db.relationship('StarSystem', foreign_keys=origin_id, backref=db.backref('jumpDepartures', lazy='dynamic'))
    destination_id = db.Column(db.Integer, db.ForeignKey('starsystem.id'))
    destination = db.relationship('StarSystem',foreign_keys=destination_id , backref=db.backref('jumpArrivals', lazy='dynamic'))
    count = db.Column(db.Integer)
    hash = db.Column(db.String(256))
    signature = db.Column(db.String(256))

    def __init__(
        fleet,
        jump_key,
        origin,
        destination,
        count,
        hash,
        signature
    ):
        if not isinstance(fleet, basestring):
            throw TypeError("Fleet is not of type BaseString")
        if not isinstance(jump_key, basestring):
            throw TypeError("jump_key is not of type BaseString")
        if not isinstance(origin, [basestring,StarSystem]):
            throw TypeError("origin is not of type BaseString or StarSystem")
        if not isinstance(destination, [basestring,StarSystem]):
            throw TypeError("destination is not of type BaseString or StarSystem")
        if not isinstance(count, int):
            throw TypeError("count is not of type int")
        if not isinstance(hash, basestring):
            throw TypeError("signature is not of type int")

        if count < 1:
            throw ValueError("jumps cannot be fewer than one")

        if isinstance(origin, basestring):
            if not util.verifyFieldIsHash(origin):
                throw ValueError("origin (of type basestring) isn't an MD5 hash")
            self.origin = db.session.query(StarLog).filter(Starlog.hash==origin).first()
        else:
            self.origin = origin

        if isinstance(destination, basestring):
            if not util.verifyFieldIsHash(destination):
                throw ValueError("destination (of type basestring) isn't an MD5 hash")
            self.destination = db.session.query(StarLog).filter(Starlog.hash==destination).first()
        else:
            self.destination = destination

        if self.destination==self.origin:
            throw ValueError("Destination and origin cannot be the same")
            
        hashed = hashlib.sha256(fleet+jump_key+self.origin+self.destination+str(count))


    def __repr__(self):
        return '<Jump %r>' % self.id
