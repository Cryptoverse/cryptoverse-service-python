import json
import util
from flask import Blueprint, request
import tasks

debug = Blueprint('debug', __name__)

@debug.route('/hash-star-log', methods=['POST'])
def hashStarLog():
	jsonData = request.get_json()
	return json.dumps(util.hashStarLog(jsonData)), 200

@debug.route("/probe-star-log", methods=['POST'])
def probeStarLog():
	jsonData = request.get_json()
	tid = tasks.probeStarLog.delay(jsonData)
	returnObject = {}
	returnObject['task_id'] = str(tid)
	return json.dumps(returnObject)

@debug.route("/probe-star-log-sync", methods=['POST'])
def probeStarLogSync():
	jsonData = request.get_json()
	task = tasks.probeStarLog.delay(jsonData)
	result = task.get()
	return json.dumps(result[1])

@debug.route('/sign', methods=['POST'])
def sign():
	jsonData = request.get_json()
	return util.rsaSign(jsonData['private_key'], jsonData['message']), 200

@debug.route('/verify-signature', methods=['POST'])
def verifySignature():
	jsonData = request.get_json()
	return 'valid' if util.rsaVerify(jsonData['public_key'], jsonData['signature'], jsonData['message']) else 'invalid'

@debug.route('/sign-jump', methods=['POST'])
def signJump():
	jsonData = request.get_json()
	message = util.concatJump(jsonData)
	signature = util.rsaSign(jsonData['private_key'], message)
	return json.dumps({
		'public_key': jsonData['public_key'],
		'fleet': jsonData['fleet'],
		'key': jsonData['key'],
		'origin': jsonData['origin'],
		'destination': jsonData['destination'],
		'count': jsonData['count'],
		'signature': signature
	}), 200

@debug.route('/verify-jump', methods=['POST'])
def verifyJump():
	jsonData = request.get_json()
	return 'valid' if util.rsaVerifyJump(jsonData) else 'invalid'

@debug.route('/unpack-difficulty', methods=['POST'])
def unpackDifficulty():
	jsonData = request.get_json()
	return util.unpackBits(int(jsonData['difficulty'])), 200

@debug.route('/unpack-hex-difficulty', methods=['POST'])
def unpackHexDifficulty():
	jsonData = request.get_json()
	return util.unpackBits(util.difficultyFromHex(jsonData['hex_difficulty'])), 200

@debug.route('/difficulty-change', methods=['POST'])
def difficultyChange():
	jsonData = request.get_json()
	return str(util.calculateDifficulty(jsonData['difficulty'], jsonData['duration'])), 200

@debug.route('/pack-difficulty', methods=['POST'])
def packDifficulty():
	jsonData = request.get_json()
	return str(util.difficultyFromTarget(jsonData['target'])), 200