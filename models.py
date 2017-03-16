import json
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
import util

Base = declarative_base()

class StarLog(Base):
	__tablename__ = 'star_logs'
	extend_existing=True

	id = Column(Integer, primary_key=True)
	hash = Column(String(64))
	height = Column(Integer)
	chain = Column(Integer)
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

	def __init__(self, jsonData, session):
		if 999999 < len(jsonData):
			raise Exception('Length of submission is not less than 1 megabyte')

		jsonStarLog = json.loads(jsonData)

		if not isinstance(jsonStarLog['log_header'], basestring):
			raise TypeError('Hash is not string')
		if not isinstance(jsonStarLog['log_header'], basestring):
			raise TypeError('log_header is wrong type')
		if not isinstance(jsonStarLog['version'], int):
			raise TypeError('version is not int')
		if not isinstance(jsonStarLog['log_header'], basestring):
			raise TypeError('log_header is not string')
		if not isinstance(jsonStarLog['version'], int):
			raise TypeError('version is not int')
		if not isinstance(jsonStarLog['previous_hash'], basestring):
			raise TypeError('previous_hash is not string')
		if not isinstance(jsonStarLog['difficulty'], int):
			raise TypeError('difficulty is not int')
		if not isinstance(jsonStarLog['nonce'], int):
			raise TypeError('nonce is not int')
		if not isinstance(jsonStarLog['time'], int):
			raise TypeError('time is not int')
		if util.getTime() < jsonStarLog['time']:
			raise ValueError('time is greater than the current time')
		if not isinstance(jsonStarLog['state_hash'], basestring):
			raise TypeError('state_hash is not string')
		if jsonStarLog['state'] is None:
			raise TypeError('state is missing')
		if not util.verifyFieldIsSha256(jsonStarLog['hash']):
			raise ValueError('hash is not a Sha256 Hash')
		if not util.verifyFieldIsSha256(jsonStarLog['previous_hash']):
			raise ValueError('previous_hash is not a Sha256 Hash')
		if not util.verifyFieldIsSha256(jsonStarLog['state_hash']):
			raise ValueError('state_hash is not a Sha256 Hash')
		if not util.verifyLogHeader(jsonStarLog):
			raise ValueError('log_header does not match provided values')
		if not util.verifySha256(jsonStarLog['hash'], jsonStarLog['log_header']):
			raise ValueError('Sha256 of log_header does not match hash')
		if not jsonStarLog['state_hash'] == util.hashState(jsonStarLog['state']):
			raise ValueError('state_hash does not match actual hash')
		if not util.verifyDifficulty(jsonStarLog['difficulty'], jsonStarLog['hash']):
			raise ValueError('hash does not meet requirements of difficulty')
		if util.isGenesisStarLogParent(jsonStarLog['previous_hash']):
			self.height = 0
			duplicateHeight = session.query(StarLog).filter_by(height=self.height).order_by(StarLog.chain.desc()).first()
			if duplicateHeight is None:
				self.chain = 0
			else:
				highestChain = session.query(StarLog).order_by(StarLog.chain.desc()).first()
				self.chain = highestChain.chain + 1
			self.difficulty = jsonStarLog['difficulty']
		else:
			previous = session.query(StarLog).filter_by(hash=jsonStarLog['previous_hash']).first()
			if previous is None:
				raise ValueError('no previous entry with hash '+jsonStarLog['previous_hash'])
			if jsonStarLog['time'] < previous.time:
				raise ValueError('time is less than previous time')
			if not session.query(StarLog).filter_by(hash=jsonStarLog['hash']).first() is None:
				raise ValueError('entry with hash %s already exists' % (jsonStarLog['hash']))
			self.height = previous.height + 1
			duplicateHeight = session.query(StarLog).filter_by(height=self.height).order_by(StarLog.chain.desc()).first()
			if duplicateHeight is None:
				self.chain = previous.chain
			elif previous.chain == duplicateHeight.chain:
				highestChain = session.query(StarLog).order_by(StarLog.chain.desc()).first()
				self.chain = highestChain.chain + 1
			else:
				self.chain = previous.chain
			# If the previous StarLog has no interval_id, that means we recalculated difficulty on it.
			self.interval_id = previous.id if previous.interval_id is None else previous.interval_id
			
			if util.isDifficultyChanging(self.height):
				intervalStart = session.query(StarLog).filter_by(id=previous.interval_id).first()
				if intervalStart is None:
					raise ValueError('unable to find interval start with id %s' % (previous.interval_id))
				duration = previous.time - intervalStart.time
				difficulty = util.calculateDifficulty(previous.difficulty, duration)
				if jsonStarLog['difficulty'] != difficulty:
					raise ValueError('difficulty does not match recalculated difficulty')
				# This lets the next in the chain know to use our id for the interval_id.
				self.interval_id = None
			elif jsonStarLog['difficulty'] != previous.difficulty:
				raise ValueError('difficulty does not match previous difficulty')
			else:
				self.difficulty = previous.difficulty
				

		

		for jump in jsonStarLog['state']['jumps']:
			if not util.rsaVerifyJump(jump):
				raise ValueError('state.jumps are invalid')

		self.hash = jsonStarLog['hash']
		self.log_header = jsonStarLog['log_header']
		self.version = jsonStarLog['version']
		self.previous_hash = jsonStarLog['previous_hash']
		self.difficulty = jsonStarLog['difficulty']
		self.nonce = jsonStarLog['nonce']
		self.time = jsonStarLog['time']
		self.state_hash = jsonStarLog['state_hash']
		self.size = len(jsonData)

	def getJson(self):
		return {
			'create_time': self.time,
			'hash': self.hash,
			'height': self.height,
			'chain': self.chain,
			'log_header': self.log_header,
			'version': self.version,
			'previous_hash': self.previous_hash,
			'difficulty': self.difficulty,
			'nonce': self.nonce,
			'time': self.time,
			'state_hash': self.state_hash
		}