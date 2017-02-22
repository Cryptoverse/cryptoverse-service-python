from __future__ import print_function
import sys
from app import db
from flask_sqlalchemy import SQLAlchemy
import hashlib
import cryptography
import json
import re
import util

class StarLog(db.Model):
    __tablename__ = "star_logs"
    extend_existing=True

    id = db.Column(db.Integer, primary_key=True)
    hash = db.Column(db.String(64))
    height = db.Column(db.Integer)
    chain = db.Column(db.Integer)
    size = db.Column(db.Integer)
    log_header = db.Column(db.String(255))
    version = db.Column(db.Integer)
    previous_hash = db.Column(db.String(64))
    difficulty = db.Column(db.Integer)
    nonce = db.Column(db.Integer)
    time = db.Column(db.Integer)
    state_hash = db.Column(db.String(64))

    def __repr__(self):
        return '<StarLog %r>' % self.hash

    def __init__(
        self,
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
            raise TypeError("Hash is not string")
        if not isinstance(log_header, basestring):
            raise TypeError("log_header is wrong type")
        if not isinstance(version, int):
            raise TypeError("version is not int")
        if not isinstance(log_header, basestring):
            raise TypeError("log_header is not string")
        if not isinstance(version, int):
            raise TypeError("version is not int")
        if not isinstance(previous_hash, basestring):
            raise TypeError("previous_hash is not string")
        if not isinstance(difficulty, int):
            raise TypeError("difficulty is not int")
        if not isinstance(nonce, int):
            raise TypeError("nonce is not int")
        if not isinstance(time, int):
            raise TypeError("time is not int")
        if not isinstance(state_hash, basestring):
            raise TypeError("state_hash is not string")
        if state is None:
            raise TypeError("state is missing")
        if not util.verifyFieldIsHash(hash):
            raise ValueError("hash is not a Sha256 Hash")
        if not util.verifyFieldIsHash(previous_hash):
            raise ValueError("previous_hash is not a Sha256 Hash")
        if not util.verifyFieldIsHash(state_hash):
            raise ValueError("state_hash is not a Sha256 Hash")
        if not util.isFirstStarLog(previous_hash):
            if StarLog.query.filter_by(hash=previous_hash).first() is None:
                raise ValueError("no previous entry with hash "+previous_hash)
            if not StarLog.query.filter_by(hash=hash).first() is None:
                raise ValueError("entry with hash "+hash+" already exists")
        if not util.verifyLogHeader(log_header, version, previous_hash, difficulty, nonce, time, state_hash):
            raise ValueError("log_header does not match provided values")
        if not util.verifyHash(hash, log_header):
            raise ValueError("Sha256 of log_header does not match hash")        
        if not util.verifyHash(state_hash, json.dumps(state, separators=(',',':'))):
            raise ValueError("state_hash does not match actual hash")
        if not util.verifyJumpSignatures(state['jumps']):
            raise ValueError("state.jumps are invalid")
            
        self.hash = hash
        self.log_header = log_header
        self.version = version
        self.previous_hash = previous_hash
        self.difficulty = difficulty
        self.nonce = nonce
        self.time = time
        self.state_hash = state_hash

    @classmethod
    def initFromJson(cls, jsonData):
        if 999999 < len(jsonData):
            raise Exception("Length of submission is not less than 1 megabyte")

        obj = json.loads(jsonData)

        starlog = cls(
            obj['hash'],
            obj['log_header'],
            obj['version'],
            obj['previous_hash'],
            obj['difficulty'],
            obj['nonce'],
            obj['time'],
            obj['state_hash'],
            obj['state'])
        
        starlog.size = len(jsonData)

        return starlog

    @classmethod
    def addFromJson(jsonData, parseJumpData=True, parseStarSystemData=True):
        sl = initFromJson(jsonData)
        db.session.add(sl)
        db.session.commit()

        jsonData = json.loads(jsonData)

        # This raises a parse error if I leave it uncommented... probably because it's trying to loop through nothing
        #if 'jumps' in jsonData:
        #    for jump in jumps:


        if 'star_systems' in jsonData:
            pass

    def getJson(self):
        return {
            'create_time': self.time,
            'hash': self.hash,
            'log_header': self.log_header,
            'version': self.version,
            'previous_hash': self.previous_hash,
            'difficulty': self.difficulty,
            'nonce': self.nonce,
            'time': self.time,
            'state_hash': self.state_hash
        }

'''
class StarSystem(db.Model):
    __tablename__ = "star_systems"
    extend_existing=True

    id = db.Column(db.Integer(), primary_key=True)
    star_log_id = db.Column(db.Integer, db.ForeignKey('star_logs.id'))
    star_log = db.relationship('StarLog', backref=db.backref('star_systems', lazy='dynamic'))
    fleet = db.Column(db.String(130))

    def __repr__(self):
        return '<StarSystem %r>' % self.id


class Deployment(db.Model):
    __tablename__ = "deployments"
    extend_existing=True

    id = db.Column(db.Integer, primary_key=True)
    star_system_id = db.Column(db.Integer, db.ForeignKey('star_systems.id'))
    star_system = db.relationship('StarSystem', backref=db.backref('deployments', lazy='dynamic'))
    fleet = db.Column(db.String(130))
    count = db.Column(db.Integer)

    def __repr__(self):
        return '<Deployment %r>' % self.id

class StarLogJump(db.Model):
    __tablename__ = "star_log_jumps"
    extend_existing=True

    id = db.Column(db.Integer, primary_key=True)
    jump_id = db.Column(db.Integer, db.ForeignKey('jumps.id'))
    jump = db.relationship('Jump', backref=db.backref('star_log_jumps', lazy='dynamic'))
    star_log_id = db.Column(db.Integer, db.ForeignKey('star_logs.id'))
    star_log = db.relationship('StarLog', backref=db.backref('star_log_jumps', lazy='dynamic'))
    index = db.Column(db.Integer)
    def __repr__(self):
        return '<StarLogJump %r>' % self.hash

    def __init__(
        self,
        jump_id,
        star_log_id,
        index
    ):
        if not isinstance(jump_id, int):
            raise TypeError("jump_id is not int")
        if not isinstance(star_log_id, int):
            raise TypeError("star_log_id is not int")
        if not isinstance(index, int):
            raise TypeError("index is not int")

        self.jump_id = jump_id
        self.star_log_id = star_log_id
        self.index = index

class Jump(db.Model):
    __tablename__ = "jumps"
    extend_existing=True

    id = db.Column(db.Integer, primary_key=True)
    fleet = db.Column(db.String(130))
    jump_key = db.Column(db.String(64))
    origin_id = db.Column(db.Integer, db.ForeignKey('star_systems.id'))
    origin = db.relationship('StarSystem', foreign_keys=origin_id, backref=db.backref('star_systems.id', lazy='dynamic'))
    destination_id = db.Column(db.Integer, db.ForeignKey('star_systems.id'))
    destination = db.relationship('StarSystem',foreign_keys=destination_id , backref=db.backref('star_systems.id', lazy='dynamic'))
    count = db.Column(db.Integer)
    hash = db.Column(db.String(64))
    signature = db.Column(db.String(255))

    def __init__(
        fleet,
        jump_key,
        origin_id,
        destination_id,
        count,
        hash,
        signature
    ):
        if not isinstance(fleet, basestring):
            raise TypeError("Fleet is not of type BaseString")
        if not isinstance(jump_key, basestring):
            raise TypeError("jump_key is not of type BaseString")
        if not isinstance(origin, [basestring,StarSystem]):
            raise TypeError("origin is not of type BaseString or StarSystem")
        if not isinstance(destination, [basestring,StarSystem]):
            raise TypeError("destination is not of type BaseString or StarSystem")
        if not isinstance(count, int):
            raise TypeError("count is not of type int")
        if not isinstance(hash, basestring):
            raise TypeError("signature is not of type int")

        if count < 1:
            raise ValueError("jumps cannot be fewer than one")

        if isinstance(origin, basestring):
            if not util.verifyFieldIsHash(origin):
                raise ValueError("origin (of type basestring) isn't an MD5 hash")
            self.origin = db.session.query(StarLog).filter(Starlog.hash==origin).first()
        else:
            self.origin = origin

        if isinstance(destination, basestring):
            if not util.verifyFieldIsHash(destination):
                raise ValueError("destination (of type basestring) isn't an MD5 hash")
            self.destination = db.session.query(StarLog).filter(Starlog.hash==destination).first()
        else:
            self.destination = destination

        if self.destination==self.origin:
            raise ValueError("Destination and origin cannot be the same")
            
        hashed = hashlib.sha256(fleet+jump_key+self.origin+self.destination+str(count))


    def __repr__(self):
        return '<Jump %r>' % self.id
'''