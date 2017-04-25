import logging
import os
import json
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS, cross_origin

starLogsMaxLimit = int(os.getenv('STARLOGS_MAX_LIMIT', '10'))
eventsMaxLimit = int(os.getenv('EVENTS_MAX_LIMIT', '10'))
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
from models import StarLog, Fleet, Chain, ChainIndex, Event, EventSignature, EventInput, EventOutput, StarLogEventSignature

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
		'ship_reward': util.shipReward,
		'star_logs_max_limit': starLogsMaxLimit,
		'events_max_limit': eventsMaxLimit,
		'chains_max_limit': chainsMaxLimit
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
		results = []

		# TODO: Remove duplicate code that's in chains and starlogs.
		# TODO: Make this code better by figuring out joins and such.
		for match in matches:
			signatureBinds = session.query(StarLogEventSignature).filter_by(star_log_id=match.id).all()
			events = []
			for signatureBind in signatureBinds:
				signatureMatch = session.query(EventSignature).filter_by(id=signatureBind.event_signature_id).first()
				fleet = session.query(Fleet).filter_by(id=signatureMatch.fleet_id).first()
				inputEvents = session.query(EventInput).filter_by(event_signature_id=signatureMatch.id).all()
				outputEvents = session.query(EventOutput).filter_by(event_signature_id=signatureMatch.id).all()

				inputs = []
				for currentInput in inputEvents:
					currentInputEvent = session.query(Event).filter_by(id=currentInput.event_id).first()
					inputs.append(currentInput.getJson(currentInputEvent.key))
				
				outputs = []
				for currentOutput in outputEvents:
					currentOutputEvent = session.query(Event).filter_by(id=currentOutput.event_id).first()
					outputFleet = session.query(Fleet).filter_by(id=currentOutputEvent.fleet_id).first()
					outputStarSystem = session.query(StarLog).filter_by(id=currentOutputEvent.star_system_id).first()
					# Rewards sent to the probed system can't have been known, so they would be left blank.
					outputStarSystemHash = None if outputStarSystem.hash == match.hash else outputStarSystem.hash
					outputs.append(currentOutput.getJson(util.getEventTypeName(currentOutputEvent.type_id), outputFleet.hash, currentOutputEvent.key, outputStarSystemHash, currentOutputEvent.count))
				events.append(signatureMatch.getJson(fleet.hash, fleet.public_key, inputs, outputs, signatureBind.index))
			results.append(match.getJson(events))

		return json.dumps(results)
	finally:
		session.close()

@app.route('/star-logs')
def getStarLogs():
	
	session = database.session()
	try:
		previousHash = request.args.get('previous_hash', None, type=str)
		beforeTime = request.args.get('before_time', None, type=int)
		sinceTime = request.args.get('since_time', None, type=int)
		limit = request.args.get('limit', 1, type=int)
		offset = request.args.get('offset', None, type=int)
		query = session.query(StarLog).order_by(StarLog.time.desc())
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
		results = []
		# TODO: Remove duplicate code that's in chains and starlogs.
		# TODO: Make this code better by figuring out joins and such.
		for match in matches:
			signatureBinds = session.query(StarLogEventSignature).filter_by(star_log_id=match.id).all()
			events = []
			for signatureBind in signatureBinds:
				signatureMatch = session.query(EventSignature).filter_by(id=signatureBind.event_signature_id).first()
				fleet = session.query(Fleet).filter_by(id=signatureMatch.fleet_id).first()
				inputEvents = session.query(EventInput).filter_by(event_signature_id=signatureMatch.id).all()
				outputEvents = session.query(EventOutput).filter_by(event_signature_id=signatureMatch.id).all()

				inputs = []
				for currentInput in inputEvents:
					currentInputEvent = session.query(Event).filter_by(id=currentInput.event_id).first()
					inputs.append(currentInput.getJson(currentInputEvent.key))
				
				outputs = []
				for currentOutput in outputEvents:
					currentOutputEvent = session.query(Event).filter_by(id=currentOutput.event_id).first()
					outputFleet = session.query(Fleet).filter_by(id=currentOutputEvent.fleet_id).first()
					outputStarSystem = session.query(StarLog).filter_by(id=currentOutputEvent.star_system_id).first()
					# Rewards sent to the probed system can't have been known, so they would be left blank.
					outputStarSystemHash = None if outputStarSystem.hash == match.hash else outputStarSystem.hash
					outputs.append(currentOutput.getJson(util.getEventTypeName(currentOutputEvent.type_id), outputFleet.hash, currentOutputEvent.key, outputStarSystemHash, currentOutputEvent.count))
				events.append(signatureMatch.getJson(fleet.hash, fleet.public_key, inputs, outputs, signatureBind.index))
			results.append(match.getJson(events))
		return json.dumps(results)
	finally:
		session.close()

@app.route('/star-logs', methods=['POST'])
def postStarLogs():
	session = database.session()
	try:
		validate.byteSize(util.maximumStarLogSize, request.data)
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

		needsStarLogIds = [chainIndex, chain]
		needsStarSystemIds = []

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

		fleetsAdded = False
		for fleet in util.getFleets(starLogJson['events']):
			fleetHash, fleetPublicKey = fleet
			if session.query(Fleet).filter_by(hash=fleetHash).first() is None:
				session.add(Fleet(fleetHash, fleetPublicKey))
				fleetsAdded = True
		
		if fleetsAdded:
			session.commit()

		for currentEvent in starLogJson['events']:
			existingSignature = session.query(EventSignature).filter_by(hash=currentEvent['hash']).first()
			if existingSignature:
				additionalSignatureBind = StarLogEventSignature(existingSignature.id, None, currentEvent['index'])
				session.add(additionalSignatureBind)
				needsStarLogIds.append(additionalSignatureBind)
				continue
			fleet = session.query(Fleet).filter_by(hash=currentEvent['fleet_hash']).first()
			eventSignature = EventSignature(util.getEventTypeId(currentEvent['type']), fleet.id, currentEvent['hash'], currentEvent['signature'], util.getTime(), 1)
			session.add(eventSignature)
			session.commit()
			eventSignatureBind = StarLogEventSignature(eventSignature.id, None, currentEvent['index'])
			session.add(eventSignatureBind)
			needsStarLogIds.append(eventSignatureBind)

			for currentInput in currentEvent['inputs']:
				targetInput = session.query(Event).filter_by(key=currentInput['key']).first()
				if targetInput is None:
					raise Exception('event %s is not accounted for' % currentInput['key'])
				eventInput = EventInput(targetInput.id, eventSignature.id, currentInput['index'])
				session.add(eventInput)
			for currentOutput in currentEvent['outputs']:
				targetOutput = session.query(Event).filter_by(key=currentOutput['key']).first()
				if targetOutput is None:
					outputFleet = session.query(Fleet).filter_by(hash=currentOutput['fleet_hash']).first()
					if outputFleet is None:
						outputFleet = Fleet(currentOutput['fleet_hash'], None)
						session.add(outputFleet)
						session.commit()
					targetStarSystemId = None
					if currentOutput['star_system']:
						targetStarSystem = session.query(StarLog).filter_by(hash=currentOutput['star_system']).first()
						if targetStarSystem is None:
							raise Exception('star system %s is not accounted for' % currentOutput['star_system'])
						targetStarSystemId = targetStarSystem.id
					targetOutput = Event(currentOutput['key'], util.getEventTypeId(currentOutput['type']), outputFleet.id, currentOutput['count'], targetStarSystemId)
					session.add(targetOutput)
					session.commit()
					if targetStarSystemId is None:
						needsStarSystemIds.append(targetOutput)
				eventOutput = EventOutput(targetOutput.id, eventSignature.id, currentOutput['index'])
				session.add(eventOutput)

		starLog = StarLog(starLogJson['hash'], chainIndex.id, height, len(request.data), starLogJson['log_header'], starLogJson['version'], starLogJson['previous_hash'], starLogJson['difficulty'], starLogJson['nonce'], starLogJson['time'], starLogJson['events_hash'], intervalId)
		session.add(starLog)
		session.commit()
		for entry in needsStarLogIds:
			entry.star_log_id = starLog.id
		for entry in needsStarSystemIds:
			entry.star_system_id = starLog.id
		session.commit()
	except:
		session.rollback()
		raise
	finally:
		session.close()
	return '200', 200

@app.route('/events')
def getEvents():
	session = database.session()
	try:
		limit = request.args.get('limit', 1, type=int)

		if eventsMaxLimit < limit:
			raise ValueError('limit greater than maximum allowed')

		# Don't get reward event signatures, since they'll always be associated with an existing block.
		# TODO: Order by confirmation counts, less confirmations should appear first.
		signatures = session.query(EventSignature).order_by(EventSignature.time.desc()).filter(EventSignature.type_id != util.getEventTypeId('reward')).limit(limit)
		results = []

		for signature in signatures:
			fleet = session.query(Fleet).filter_by(id=signature.fleet_id).first()

			inputs = []
			for currentInput in session.query(EventInput).filter_by(event_signature_id=signature.id).all():
				currentInputEvent = session.query(Event).filter_by(id=currentInput.event_id).first()
				inputs.append(currentInput.getJson(currentInputEvent.key))
			
			outputs = []
			for currentOutput in session.query(EventOutput).filter_by(event_signature_id=signature.id).all():
				currentOutputEvent = session.query(Event).filter_by(id=currentOutput.event_id).first()
				outputFleet = session.query(Fleet).filter_by(id=currentOutputEvent.fleet_id).first()
				outputStarSystem = session.query(StarLog).filter_by(id=currentOutputEvent.star_system_id).first()
				outputs.append(currentOutput.getJson(util.getEventTypeName(currentOutputEvent.type_id), outputFleet.hash, currentOutputEvent.key, outputStarSystem.hash, currentOutputEvent.count))
			
			results.append(signature.getJson(fleet.hash, fleet.public_key, inputs, outputs, None))
		return json.dumps(results)
	finally:
		session.close()

@app.route('/events', methods=['POST'])
def postEvents():
	session = database.session()
	try:
		validate.byteSize(util.maximumEventSize, request.data)
		eventJson = json.loads(request.data)
		validate.event(eventJson, False, True, False)

		if session.query(EventSignature).filter_by(hash=eventJson['hash']).first():
			raise Exception('event with hash %s already exists' % eventJson['hash'])

		fleet = session.query(Fleet).filter_by(hash=eventJson['fleet_hash']).first()

		eventSignature = EventSignature(util.getEventTypeId(eventJson['type']), fleet.id, eventJson['hash'], eventJson['signature'], util.getTime(), 0)
		session.add(eventSignature)
		session.commit()

		usedInputs = []
		
		for currentInput in eventJson['inputs']:
			inputEvent = session.query(Event).filter_by(key=currentInput['key']).first()
			if inputEvent is None:
				raise Exception('event with key %s not accounted for' % currentInput['key'])
		for currentOutput in eventJson['outputs']:
			targetOutput = session.query(Event).filter_by(key=currentOutput['key']).first()
			if targetOutput is not None:
				outputFleet = session.query(Fleet).filter_by(hash=currentOutput['fleet_hash']).first()
				if outputFleet is None:
					outputFleet = Fleet(currentOutput['fleet_hash'], None)
					session.add(outputFleet)
					session.commit()
				targetStarSystem = session.query(StarLog).filter_by(hash=currentOutput['star_system']).first()
				if targetStarSystem is None:
					raise Exception('star system %s is not accounted for' % currentOutput['star_system'])
				
				targetOutput = Event(currentOutput['key'], util.getEventTypeId(currentOutput['type']), outputFleet.id, currentOutput['count'], targetStarSystem.id)
				session.add(targetOutput)
				session.commit()
			eventOutput = EventOutput(targetOutput.id, eventSignature.id, currentOutput['index'])
			session.add(eventOutput)
			
	except:
		session.rollback()
		raise
	finally:
		session.close()

	return '200', 200

if isDebug:
	from debug import debug
	app.register_blueprint(debug, url_prefix='/debug')

if __name__ == '__main__':
	if 0 < util.difficultyFudge:
		app.logger.info('All hash difficulties will be calculated with DIFFICULTY_FUDGE %s' % (util.difficultyFudge))
	app.run(use_reloader = False)
