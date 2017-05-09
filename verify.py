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