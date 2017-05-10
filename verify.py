import util
from models import StarLog

def jump(session, fleet, inputs, outputs):
	if len(inputs) == 0:
		raise Exception('jump must contain at least one input')
	if len(outputs) == 0:
		raise Exception('jump must contain at least oun output')
	inputShipCount = 0
	originSystemId = inputs[0].star_system_id
	for currentInput in inputs:
		if currentInput.fleet_id != fleet.id:
			raise Exception('jump must consist of ships from a single fleet')
		if currentInput.star_system_id != originSystemId:
			raise Exception('jump inputs must start from the same origin')
		inputShipCount += currentInput.count
	outputShipCount = 0
	destinationSystemId = None
	for currentOutput in outputs:
		if currentOutput.star_system_id != originSystemId:
			destinationSystemId = currentOutput.star_system_id
			break
	if destinationSystemId is None:
		raise Exception('jump must consist of at least one output in another system')
	for currentOutput in outputs:
		if currentOutput.fleet_id != fleet.id:
			raise Exception('jump must consist of ships from a single fleet')
		if currentOutput.star_system_id == originSystemId:
			inputShipCount -= currentOutput.count
		elif currentOutput.star_system_id == destinationSystemId:
			outputShipCount += currentOutput.count
		else:
			raise Exception('jump outputs must end in the same origin or destination')
	originSystem = session.query(StarLog).filter_by(id=originSystemId).first()
	destinationSystem = session.query(StarLog).filter_by(id=destinationSystemId).first()
	shipCost = util.getJumpCost(originSystem.hash, destinationSystem.hash, inputShipCount)
	if shipCost == inputShipCount:
		raise Exception('jump cannot have zero ships reach destination')
	if shipCost != (inputShipCount - outputShipCount):
		raise Exception('jump cost does not match expected cost of %s' % shipCost)

def attack(fleet, inputs, outputs):
	if len(inputs) < 2:
		raise Exception('jump must contain at least two inputs')
	
	shipCount = 0
	enemyShipCount = 0
	originSystemId = inputs[0].star_system_id
	enemyFleetId = None
	for currentInput in inputs:
		if currentInput.star_system_id != originSystemId:
			raise Exception('attack inputs must be from the same origin')
		if currentInput.fleet_id == fleet.id:
			shipCount += currentInput.count
		else:
			if enemyFleetId is None:
				enemyFleetId = currentInput.fleet_id
			elif enemyFleetId != currentInput.fleet_id:
				raise Exception('an attack may only consist of two fleets')
			enemyShipCount += currentInput.count
		
	outputShipCount = 0
	outputEnemyShipCount = 0
	for currentOutput in outputs:
		if currentOutput.count == 0:
			raise Exception('attack output cannot be zero')
		if currentOutput.star_system_id != originSystemId:
			raise Exception('attack outputs must be in the same origin')
		if currentOutput.fleet_id == fleet.id:
			outputShipCount += currentOutput.count
		elif currentOutput.fleet_id == enemyFleetId:
			outputEnemyShipCount += currentOutput.count
		else:
			raise Exception('an attack output must be from the original fleets')
	
	if shipCount < enemyShipCount:
		if enemyShipCount - shipCount != outputEnemyShipCount:
			raise Exception('attack input and output count mismatch')
	elif enemyShipCount < shipCount:
		if shipCount - enemyShipCount != outputShipCount:
			raise Exception('attack input and output count mismatch')
	elif outputShipCount + outputEnemyShipCount != 0:
		raise Exception('attack input and output count mismatch')
	