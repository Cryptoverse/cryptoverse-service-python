import json
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
import util
import validate

Base = declarative_base()

class StarLog(Base):
	__tablename__ = 'star_logs'
	extend_existing=True

	id = Column(Integer, primary_key=True)
	hash = Column(String(64))
	chain = Column(Integer)
	height = Column(Integer)
	size = Column(Integer)
	log_header = Column(String(255))
	version = Column(Integer)
	previous_hash = Column(String(64))
	difficulty = Column(Integer)
	nonce = Column(Integer)
	time = Column(Integer)
	state_hash = Column(String(64))
	interval_id = Column(Integer)

	def __repr__(self):
		return '<StarLog %r>' % self.hash

	def __init__(self, hash, chain, height, size, log_header, version, previous_hash, difficulty, nonce, time, state_hash, interval_id):
		self.hash = hash
		self.chain = chain
		self.height = height
		self.size = size
		self.log_header = log_header
		self.version = version
		self.previous_hash = previous_hash
		self.difficulty = difficulty
		self.nonce = nonce
		self.time = time
		self.state_hash = state_hash
		self.interval_id = interval_id

	def getJson(self):
		jumps = []
		# TODO: Get Jumps
		starSystems = []
		# TODO: Get Star Systems

		return {
			'create_time': self.time,
			'hash': self.hash,
			'height': self.height,
			'log_header': self.log_header,
			'version': self.version,
			'previous_hash': self.previous_hash,
			'difficulty': self.difficulty,
			'nonce': self.nonce,
			'time': self.time,
			'state_hash': self.state_hash,
			'state': {
				'jumps': jumps,
				'star_systems': starSystems
			}
		}

class Chain(Base):
	__tablename__ = 'chains'
	extend_existing=True

	id = Column(Integer, primary_key=True)
	root_id = Column(Integer)
	previous_id = Column(Integer)
	star_log_id = Column(Integer)
	previous_star_log_id = Column(Integer)
	hash = Column(String(64))
	previous_hash = Column(String(64))
	height = Column(Integer)
	chain = Column(Integer)
	
	def __repr__(self):
		return '<Chain %s>' % self.id

	def __init__(self, root_id, previous_id, star_log_id, previous_star_log_id, hash, previous_hash, height, chain):
		self.root_id = root_id
		self.previous_id = previous_id
		self.star_log_id = star_log_id
		self.previous_star_log_id = previous_star_log_id
		self.hash = hash
		self.previous_hash = previous_hash
		self.height = height
		self.chain = chain

	def getJson(self):
		return {
			'hash': self.hash,
			'previous_hash': self.previous_hash,
			'height': self.height
		}

class Fleet(Base):
	__tablename__ = 'fleets'
	extend_existing=True

	id = Column(Integer, primary_key=True)
	hash = Column(String(64))
	public_key = Column(String(398))
	
	def __repr__(self):
		return '<Fleet %r>' % self.id

	def __init__(self, hash, public_key):
		self.hash = hash
		self.public_key = public_key

	def getJson(self):
		return {
			'hash': self.hash,
			'public_key': self.public_key
		}

class Jump(Base):
	__tablename__ = 'jumps'
	extend_existing=True

	id = Column(Integer, primary_key=True)
	fleet_id = Column(String(130))
	origin_id = Column(Integer)
	destination_id = Column(Integer)
	key = Column(String(64))
	count = Column(Integer)
	lost_count = Column(Integer)
	signature = Column(String(255))
	
	def __repr__(self):
		return '<Jump %r>' % self.id

	def __init__(self, fleet_id, origin_id, destination_id, key, count, lost_count, signature):
		self.fleet_id = fleet_id
		self.origin_id = origin_id
		self.destination_id = destination_id
		self.key = key
		self.count = count
		self.lost_count = lost_count
		self.signature = signature

	def getJson(self, session):
		# TODO: Retrieve the hashes for the origin and destination from the database
		# TODO: Include the create time...
		origin = None
		destination = None
		create_time = None

		return {
			'create_time': create_time,
			'fleet_id': self.fleet,
			'key': self.jump_key,
			'origin': origin,
			'destination': destination,
			'count': self.count,
			'signature': self.signature
		}