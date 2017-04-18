from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class StarLog(Base):
	__tablename__ = 'star_logs'
	extend_existing=True

	id = Column(Integer, primary_key=True)
	hash = Column(String(64))
	chain_index_id = Column(Integer, ForeignKey('chain_indices.id'))
	height = Column(Integer)
	size = Column(Integer)
	log_header = Column(String(255))
	version = Column(Integer)
	previous_hash = Column(String(64))
	difficulty = Column(Integer)
	nonce = Column(Integer)
	time = Column(Integer)
	events_hash = Column(String(64))
	interval_id = Column(Integer, ForeignKey('star_logs.id'))

	def __repr__(self):
		return '<StarLog %r>' % self.hash

	def __init__(self, hash, chain_index_id, height, size, log_header, version, previous_hash, difficulty, nonce, time, events_hash, interval_id):
		self.hash = hash
		self.chain_index_id = chain_index_id
		self.height = height
		self.size = size
		self.log_header = log_header
		self.version = version
		self.previous_hash = previous_hash
		self.difficulty = difficulty
		self.nonce = nonce
		self.time = time
		self.events_hash = events_hash
		self.interval_id = interval_id

	def getJson(self, events=[]):
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
			'events_hash': self.state_hash,
			'events': events
		}

class ChainIndex(Base):
	__tablename__ = 'chain_indices'
	extend_existing=True

	id = Column(Integer, primary_key=True)
	root_id = Column(Integer, ForeignKey('chain_indices.id'))
	previous_id = Column(Integer, ForeignKey('chain_indices.id'))
	star_log_id = Column(Integer, ForeignKey('star_logs.id'))
	previous_star_log_id = Column(Integer, ForeignKey('star_logs.id'))
	hash = Column(String(64))
	previous_hash = Column(String(64))
	height = Column(Integer)
	chain = Column(Integer)

	def __repr__(self):
		return '<Chain Index %s>' % self.id

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

class Chain(Base):
	__tablename__ = 'chains'
	extend_existing=True

	id = Column(Integer, primary_key=True)
	height = Column(Integer)
	head_index_id = Column(Integer)
	chain = Column(Integer)
	star_log_id = Column(Integer)
	
	def __repr__(self):
		return '<Chain %s>' % self.id

	def __init__(self, height, head_index_id, chain, star_log_id):
		self.height = height
		self.head_index_id = head_index_id
		self.chain = chain
		self.star_log_id = star_log_id

	def getJson(self):
		return {
			'height': self.height,
			'chain': self.chain
		}

class Fleet(Base):
	__tablename__ = 'fleets'
	extend_existing=True

	id = Column(Integer, primary_key=True)
	hash = Column(String(64))
	public_key = Column(String(392))
	
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

class Event(Base):
	__tablename__ = 'events'
	extend_existing=True

	id = Column(Integer, primary_key=True)
	key = Column(String(64))
	signature = Column(String(512))
	event_type_id = Column(Integer)
	fleet_id = Column(Integer, ForeignKey('fleets.id'))
	count = Column(Integer)
	star_log_id = Column(Integer, ForeignKey('star_logs.id'))
	
	def __repr__(self):
		return '<Event %s>' % self.id

	def __init__(self, key, signature, event_type_id, fleet_id, count, star_log_id):
		self.key = key
		self.signature = signature
		self.event_type_id = event_type_id
		self.fleet_id = fleet_id
		self.count = count
		self.star_log_id = star_log_id

	def getJson(self):
		return {
			'key': self.key
		}