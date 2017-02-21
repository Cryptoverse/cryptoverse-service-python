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
    discovery_hash = db.Column(db.String(64))

    def __repr__(self):
        return '<StarLog %r>' % self.hash

    def __init__(
        id,
        hash,
        height,
        chain,
        size,
        log_header,
        version,
        previous_hash,
        difficulty,
        nonce,
        time,
        discovery_hash
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
        if not isinstance(state, basestring):
            raise TypeError("state is not string")

        if not util.verifyFieldIsHash(hash):
            raise ValueError("hash is not a MD5 Hash")
        if not util.verifyFieldIsHash(previous_hash):
            raise ValueError("previous_hash is not a MD5 Hash")
        if not util.verifyFieldIsHash(state_hash):
            raise ValueError("state_hash is not a MD5 Hash")

        self.id = id
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
            obj['id'],
            obj['hash'],
            obj['height'],
            obj['chain'],
            obj['size'],
            obj['log_header'],
            obj['version'],
            obj['previous_hash'],
            obj['difficulty'],
            obj['nonce'],
            obj['time'],
            obj['discovery_hash'])

        return starlog

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



class StarSystem(db.Model):
    __tablename__ = "star_systems"
    id = db.Column(db.Integer(), primary_key=True)
    star_log_id = db.Column(db.Integer, db.ForeignKey('star_logs.id'))
    star_log = db.relationship('StarLog', backref=db.backref('star_systems', lazy='dynamic'))
    fleet = db.Column(db.String(130))

    def __repr__(self):
        return '<StarSystem %r>' % self.id


class Deployment(db.Model):
    __tablename__ = "deployments"
    id = db.Column(db.Integer, primary_key=True)
    star_system_id = db.Column(db.Integer, db.ForeignKey('star_systems.id'))
    star_system = db.relationship('StarSystem', backref=db.backref('deployments', lazy='dynamic'))
    fleet = db.Column(db.String(130))
    count = db.Column(db.Integer)

    def __repr__(self):
        return '<Deployment %r>' % self.id

'''
class Jump(db.Model):
    __tablename__ = "jumps"
    id = db.Column(db.Integer, primary_key=True)
    fleet = db.Column(db.String(130))
    jump_key = db.Column(db.String(64))
    origin_id = db.Column(db.Integer, db.ForeignKey('star_systems.id'))
    origin = db.relationship('StarSystem', foreign_keys=origin_id, backref=db.backref('star_systems.id', lazy='dynamic'))
    #origin = db.relationship('StarSystem', foreign_keys=origin_id, backref=db.backref('jumpDepartures', lazy='dynamic'))
    destination_id = db.Column(db.Integer, db.ForeignKey('star_systems.id'))
    destination = db.relationship('StarSystem',foreign_keys=destination_id , backref=db.backref('star_systems.id', lazy='dynamic'))
    #destination = db.relationship('StarSystem',foreign_keys=destination_id , backref=db.backref('jumpArrivals', lazy='dynamic'))
    count = db.Column(db.Integer)
    hash = db.Column(db.String(64))
    signature = db.Column(db.String(255))

    def __init__(
        id,
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