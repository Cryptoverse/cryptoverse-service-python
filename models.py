import json
from app import app, db # pylint: disable=locally-disabled, unused-import
import util

class StarLog(db.Model):
	__tablename__ = 'star_logs'
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
	interval_id = db.Column(db.Integer)

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
	__tablename__ = 'star_systems'
	extend_existing=True

	id = db.Column(db.Integer(), primary_key=True)
	star_log_id = db.Column(db.Integer, db.ForeignKey('star_logs.id'))
	star_log = db.relationship('StarLog', backref=db.backref('star_systems', lazy='dynamic'))
	fleet = db.Column(db.String(130))

	def __repr__(self):
		return '<StarSystem %r>' % self.id


class Deployment(db.Model):
	__tablename__ = 'deployments'
	extend_existing=True

	id = db.Column(db.Integer, primary_key=True)
	star_system_id = db.Column(db.Integer, db.ForeignKey('star_systems.id'))
	star_system = db.relationship('StarSystem', backref=db.backref('deployments', lazy='dynamic'))
	fleet = db.Column(db.String(130))
	count = db.Column(db.Integer)

	def __repr__(self):
		return '<Deployment %r>' % self.id

class StarLogJump(db.Model):
	__tablename__ = 'star_log_jumps'
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
			raise TypeError('jump_id is not int')
		if not isinstance(star_log_id, int):
			raise TypeError('star_log_id is not int')
		if not isinstance(index, int):
			raise TypeError('index is not int')

		self.jump_id = jump_id
		self.star_log_id = star_log_id
		self.index = index

class Jump(db.Model):
	__tablename__ = 'jumps'
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
			raise TypeError('Fleet is not of type BaseString')
		if not isinstance(jump_key, basestring):
			raise TypeError('jump_key is not of type BaseString')
		if not isinstance(origin, [basestring,StarSystem]):
			raise TypeError('origin is not of type BaseString or StarSystem')
		if not isinstance(destination, [basestring,StarSystem]):
			raise TypeError('destination is not of type BaseString or StarSystem')
		if not isinstance(count, int):
			raise TypeError('count is not of type int')
		if not isinstance(hash, basestring):
			raise TypeError('signature is not of type int')

		if count < 1:
			raise ValueError('jumps cannot be fewer than one')

		if isinstance(origin, basestring):
			if not util.verifyFieldIsHash(origin):
				raise ValueError('origin (of type basestring) isn't an MD5 hash')
			self.origin = db.session.query(StarLog).filter(Starlog.hash==origin).first()
		else:
			self.origin = origin

		if isinstance(destination, basestring):
			if not util.verifyFieldIsHash(destination):
				raise ValueError('destination (of type basestring) isn't an MD5 hash')
			self.destination = db.session.query(StarLog).filter(Starlog.hash==destination).first()
		else:
			self.destination = destination

		if self.destination==self.origin:
			raise ValueError('Destination and origin cannot be the same')
			
		hashed = hashlib.sha256(fleet+jump_key+self.origin+self.destination+str(count))


	def __repr__(self):
		return '<Jump %r>' % self.id
'''