import logging
import os
import json
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS, cross_origin

starLogsMaxLimit = int(os.getenv('STARLOG_MAX_LIMIT', '10'))
chainsMaxLimit = int(os.getenv('CHAINS_MAX_LIMIT', '10'))
isDebug = 0 < os.getenv('CV_DEBUG', 0)

app = Flask(__name__)
app.debug = isDebug
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DB_HOST']
database = SQLAlchemy(app)
CORS(app)

import util
import validate
from tasks import tasker
from models import StarLog, Fleet, Chain, ChainIndex

@app.before_first_request
def setupLogging():
	if not app.debug:
		# In production mode, add log handler to sys.stderr.
		app.logger.addHandler(logging.StreamHandler())
		app.logger.setLevel(logging.INFO)

@app.route('/')
def routeIndex():
	return 'Running'

@app.route("/rules")
def getRules():
	return json.dumps({
		'difficulty_fudge': util.difficultyFudge,
		'difficulty_duration': util.difficultyDuration,
		'difficulty_interval': util.difficultyInterval,
		'difficulty_start': util.difficultyStart,
		'ship_reward': util.shipReward
	})

@app.route("/jobprogress")
@cross_origin()
def poll_state():
	if 'job' in request.args:
		job_id = request.args['job']
	else:
		return 'No job id given.'

	job = tasker.AsyncResult(job_id)
	data = job.result or job.state
	# meta = json.dumps(job.info)
	if data is None:
		return "{}"
	return str(json.dumps(data))

@app.route('/chains')
def getChains():
	session = database.session()
	try:
		height = request.args.get('height', None, type=int)
		limit = request.args.get('limit', 1, type=int)
		query = database.session.query(StarLog)
		if height is None:
			query = query.order_by(StarLog.height.desc())
		else:
			if height < 0:
				raise ValueError('height is out of range')
			query = query.filter_by(height=height)
		if chainsMaxLimit < limit:
			raise ValueError('limit greater than maximum allowed')
		query = query.limit(limit)
		matches = query.all()
		result = []
		for match in matches:
			# TODO: Make this code better by figuring out joins and such.
			result = []
			# jumpMatches = session.query(StarLogJump).filter_by(star_log_id=match.id).all()
			# jumps = []
			# for jumpMatch in jumpMatches:
			# 	jump = session.query(Jump).filter_by(id=jumpMatch.jump_id).first()
			# 	origin = session.query(StarLog).filter_by(id=jump.origin_id).first()
			# 	destination = session.query(StarLog).filter_by(id=jump.destination_id).first()
			# 	fleet = session.query(Fleet).filter_by(id=jump.fleet_id).first()
			# 	origin = None if origin is None else origin.hash
			# 	destination = None if destination is None else destination.hash
			# 	fleetHash = None
			# 	fleetKey = None
			# 	if fleet is not None:
			# 		fleetHash = fleet.hash
			# 		fleetKey = fleet.public_key
			# 	jumps.append(jump.getJson(fleetHash, fleetKey, origin, destination))
			# result.append(match.getJson(jumps))
		return json.dumps(result)
	finally:
		session.close()

@app.route('/star-logs')
def getStarLogs():
	previousHash = request.args.get('previous_hash', None, type=str)
	beforeTime = request.args.get('before_time', None, type=int)
	sinceTime = request.args.get('since_time', None, type=int)
	limit = request.args.get('limit', 1, type=int)
	offset = request.args.get('offset', None, type=int)
	query = database.session.query(StarLog)
	if previousHash is not None:
		validate.fieldIsSha256(previousHash, 'previous_hash')
		query = query.filter_by(previous_hash=previousHash)
	if beforeTime is not None:
		query = query.filter(StarLog.time < beforeTime)
	if sinceTime is not None:
		query = query.filter(sinceTime < StarLog.time)
	if sinceTime is not None and beforeTime is not None and beforeTime < sinceTime:
		raise ValueError('since_time is greater than before_time')
	if starLogsMaxLimit < limit:
		raise ValueError('limit greater than maximum allowed')
	if offset is not None:
		query = query.offset(offset)

	query = query.limit(limit)
	matches = query.all()
	result = []
	for match in matches:
		result.append(match.getJson())
	return json.dumps(result)

@app.route('/star-logs', methods=['POST'])
def postStarLogs():
	session = database.session()
	try:
		validate.byteSize(999999, request.data)
		starLogJson = json.loads(request.data)
		validate.starLog(starLogJson)

		previousChain = None
		previousHash = starLogJson['previous_hash']
		isGenesis = util.isGenesisStarLog(previousHash)
		if not isGenesis:
			previousChain = session.query(ChainIndex).filter_by(hash=previousHash).first()
			if previousChain is None:
				raise ValueError('previous starlog with hash %s cannot be found' % previousHash)

		chainIndex = session.query(ChainIndex).filter_by(hash=starLogJson['hash']).first()
		if chainIndex:
			raise ValueError('starlog with hash %s already exists' % chainIndex.hash)
		
		highestChain = session.query(Chain).order_by(Chain.chain.desc()).first()
		rootId = None
		previousChainId = None
		previousStarLogId = None
		height = 0
		chainCount = 0

		if isGenesis:
			chainCount = 0 if highestChain is None else highestChain.chain + 1
		else:
			rootId = previousChain.id if previousChain.root_id is None else previousChain.root_id
			previousChainId = previousChain.id
			previousStarLogId = previousChain.star_log_id
			height = previousChain.height + 1
			chainCount = previousChain.chain
		
		chain = None

		if session.query(ChainIndex).filter_by(height=height, chain=chainCount).first():
			# A sibling chain is being created.
			rootId = None if isGenesis else previousChain.id
			chainCount = highestChain.chain + 1
			chain = Chain(height, None, chainCount, None)
			session.add(chain)
		elif isGenesis:
			chain = Chain(height, None, chainCount, None)
			session.add(chain)
		else:
			chain = session.query(Chain).filter_by(chain=chainCount).first()
			if chain is None:
				raise ValueError('no chain %s exists' % chainCount)
			chain.height = height

		chainIndex = ChainIndex(rootId, previousChainId, None, previousStarLogId, starLogJson['hash'], starLogJson['previous_hash'], height, chainCount)
		session.add(chainIndex)
		session.commit()
		chain.head_index_id = chainIndex.id

		previousStarLog = None if previousStarLogId is None else session.query(StarLog).filter_by(id=previousStarLogId).first()

		# If the previous StarLog has no interval_id, that means we recalculated difficulty on it.
		intervalId = None if previousStarLog is None else previousStarLog.interval_id

		if isGenesis:
			if starLogJson['difficulty'] != util.difficultyStart:
				raise ValueError('difficulty for genesis starlog does not match starting difficulty')
		elif util.isDifficultyChanging(height):
			intervalStart = session.query(StarLog).filter_by(id=previousStarLog.interval_id).first()
			if intervalStart is None:
				raise ValueError('unable to find interval start with id %s' % (previousStarLog.interval_id))
			duration = previousStarLog.time - intervalStart.time
			difficulty = util.calculateDifficulty(previousStarLog.difficulty, duration)
			if starLogJson['difficulty'] != difficulty:
				raise ValueError('difficulty does not match recalculated difficulty')
			# This lets the next in the chain know to use our id for the interval_id.
			intervalId = None
		elif starLogJson['difficulty'] != previousStarLog.difficulty:
			raise ValueError('difficulty does not match previous difficulty')

		for fleet in util.getFleets(starLogJson['events']):
			fleetHash, fleetPublicKey = fleet
			if session.query(Fleet).filter_by(hash=fleetHash).first() is None:
				session.add(Fleet(fleetHash, fleetPublicKey))
		
		starLog = StarLog(starLogJson['hash'], chainIndex.id, height, len(request.data), starLogJson['log_header'], starLogJson['version'], starLogJson['previous_hash'], starLogJson['difficulty'], starLogJson['nonce'], starLogJson['time'], starLogJson['events_hash'], intervalId)
		session.add(starLog)
		session.commit()
		chainIndex.star_log_id = starLog.id
		chain.star_log_id = starLog.id
		session.commit()
	except:
		session.rollback()
		raise
	finally:
		session.close()

	# database.session.add(posted)
	# database.session.commit()
	return '200', 200

@app.route('/jumps')
def getJumps():
	return 200

@app.route('/jumps', methods=['POST'])
def postJumps():
	return 200

if isDebug:
	from debug import debug
	app.register_blueprint(debug, url_prefix='/debug')

if __name__ == '__main__':
	if 0 < util.difficultyFudge:
		app.logger.info('All hash difficulties will be calculated with DIFFICULTY_FUDGE %s' % (util.difficultyFudge))
	app.run(use_reloader = False)
