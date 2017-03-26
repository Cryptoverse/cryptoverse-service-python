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
	fleet_id = Column(Integer)
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
		validate.byteSize(999999, jsonData)

		starLogJson = json.loads(jsonData)

		validate.starLog(starLogJson)

		previousFleet = None

		if util.isGenesisStarLogParent(starLogJson['previous_hash']):
			self.height = 0
			duplicateHeight = session.query(StarLog).filter_by(height=self.height).order_by(StarLog.chain.desc()).first()
			if duplicateHeight is None:
				self.chain = 0
			else:
				highestChain = session.query(StarLog).order_by(StarLog.chain.desc()).first()
				self.chain = highestChain.chain + 1
			self.difficulty = starLogJson['difficulty']
		else:
			previous = session.query(StarLog).filter_by(hash=starLogJson['previous_hash']).first()
			if previous is None:
				raise ValueError('no previous entry with hash '+starLogJson['previous_hash'])
			if starLogJson['time'] < previous.time:
				raise ValueError('time is less than previous time')
			if not session.query(StarLog).filter_by(hash=starLogJson['hash']).first() is None:
				raise ValueError('entry with hash %s already exists' % (starLogJson['hash']))
			self.height = previous.height + 1
			duplicateHeight = session.query(StarLog).filter_by(height=self.height).order_by(StarLog.chain.desc()).first()
			if duplicateHeight is None:
				self.chain = previous.chain
			elif previous.chain == duplicateHeight.chain:
				highestChain = session.query(StarLog).order_by(StarLog.chain.desc()).first()
				self.chain = highestChain.chain + 1
			else:
				highestInChain = session.query(StarLog).filter_by(chain=previous.chain).order_by(StarLog.height.desc()).first()
				if highestInChain.id == previous.id:
					self.chain = previous.chain
				else:
					highestChain = session.query(StarLog).order_by(StarLog.chain.desc()).first()
					self.chain = highestChain.chain + 1
			# If the previous StarLog has no interval_id, that means we recalculated difficulty on it.
			self.interval_id = previous.id if previous.interval_id is None else previous.interval_id
			
			if util.isDifficultyChanging(self.height):
				intervalStart = session.query(StarLog).filter_by(id=previous.interval_id).first()
				if intervalStart is None:
					raise ValueError('unable to find interval start with id %s' % (previous.interval_id))
				duration = previous.time - intervalStart.time
				difficulty = util.calculateDifficulty(previous.difficulty, duration)
				if starLogJson['difficulty'] != difficulty:
					raise ValueError('difficulty does not match recalculated difficulty')
				# This lets the next in the chain know to use our id for the interval_id.
				self.interval_id = None
			elif starLogJson['difficulty'] != previous.difficulty:
				raise ValueError('difficulty does not match previous difficulty')
			else:
				self.difficulty = previous.difficulty

			if previous.fleet_id:
				previousFleet = session.query(Fleet).filter_by(id=previous.fleet_id).first()
				if previousFleet is None:
					raise ValueError('no fleet for the previous starlog can be found')
		
		allJumps = starLogJson['state']['jumps']
		
		if previousFleet and allJumps is None:
			raise ValueError('previous fleet jump was not added to list of jumps')

		previousFleetFound = previousFleet is None
		for jump in allJumps:
			# if not previousFleetFound and jump['fleetHash'] == :

			if not validate.jumpRsa(jump):
				raise ValueError('state.jumps are invalid')

		fleetHash = starLogJson['state']['fleet']
		if fleetHash:
			existingFleet = session.query(Fleet).filter_by(hash=fleetHash).first()
			if not existingFleet:
				existingFleet = Fleet(starLogJson['state']['fleet'], None, session)
				session.add(existingFleet)
				# TODO: Move this commit out of here...
				session.commit()
			self.fleet_id = existingFleet.id

		self.hash = starLogJson['hash']
		self.log_header = util.concatStarLogHeader(starLogJson)
		self.version = starLogJson['version']
		self.previous_hash = starLogJson['previous_hash']
		self.difficulty = starLogJson['difficulty']
		self.nonce = starLogJson['nonce']
		self.time = starLogJson['time']
		self.state_hash = starLogJson['state_hash']
		self.size = len(jsonData)

	def getJson(self, session):
		fleetHash = None
		if self.fleet_id:
			fleet = session.query(Fleet).filter_by(id=self.fleet_id).first()
			if fleet:
				fleetHash = fleet.hash
		
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
				'fleet': fleetHash,
				'jumps': jumps,
				'star_systems': starSystems
			}
		}

class Fleet(Base):
	__tablename__ = 'fleets'
	extend_existing=True

	id = Column(Integer, primary_key=True)
	hash = Column(String(64))
	public_key = Column(String(398))
	
	def __repr__(self):
		return '<Fleet %r>' % self.id

	def __init__(self, publicKeyHash, publicKey, session):
		
		if not isinstance(publicKeyHash, basestring):
			raise TypeError('publicKeyHash is not string')
		validate.fieldIsSha256(publicKeyHash, 'publicKeyHash')
		if publicKey:
			if len(publicKey) != 398:
				raise ValueError('publicKey is out of range')
			if not validate.sha256(publicKeyHash, publicKey):
				raise ValueError('Sha256 of publicKey does not match publicKeyHash')
			self.public_key = publicKey
		
		self.hash = publicKeyHash
		if session.query(Fleet).filter_by(hash=self.hash).first():
			raise ValueError('the fleet publicKeyHash already exists')

	def getJson(self, session):
		return {
			'hash': self.hash,
			'public_key': self.public_key
		}

class Jump(Base):
	__tablename__ = 'jumps'
	extend_existing=True

	id = Column(Integer, primary_key=True)
	fleet = Column(String(130))
	jump_key = Column(String(64))
	origin_id = Column(Integer)
	destination_id = Column(Integer)
	count = Column(Integer)
	signature = Column(String(255))
	
	def __repr__(self):
		return '<Jump %r>' % self.id

	def __init__(self, jsonData, session):
		jsonJump = json.loads(jsonData)

		if not isinstance(jsonJump['fleet'], basestring):
			raise TypeError('fleet is not string')
		if not isinstance(jsonJump['jump_key'], basestring):
			raise TypeError('jump_key is not a string')
		if not isinstance(jsonJump['origin'], basestring):
			raise TypeError('origin is not a string')
		if not isinstance(jsonJump['destination'], basestring):
			raise TypeError('destination is not a string')
		if not isinstance(jsonJump['signature'], basestring):
			raise TypeError('signature is not a string')
		if not isinstance(jsonJump['count'], int):
			raise TypeError('count is not an integer')
		if 0 <= jsonJump['count']:
			raise ValueError('count is invalid')

	def getJson(self, session):
		# TODO: Retrieve the hashes for the origin and destination from the database
		# TODO: Include the create time...
		origin = None
		destination = None
		create_time = None

		return {
			'create_time': create_time,
			'fleet': self.fleet,
			'jump_key': self.jump_key,
			'origin': origin,
			'destination': destination,
			'count': self.count,
			'signature': self.signature
		}