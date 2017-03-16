import traceback
import json
import util
from flask import Blueprint, request
import tasks

debug = Blueprint('debug', __name__)

@debug.route("/blockchain-info", methods=['GET'])
def blockchainInfo():
	info = {}
	info['fudge'] = util.difficultyFudge
	info['difficulty_duration'] = util.difficultyDuration
	info['difficulty_interval'] = util.difficultyInterval
	return json.dumps(info)

@debug.route('/hash-star-log', methods=['POST'])
def routeDebugHashStarLog():
	try:
		jsonData = request.get_json()
		return json.dumps(util.hashStarLog(jsonData)), 200
	except:
		traceback.print_exc()
		return '400', 400

@debug.route("/probe-star-log", methods=['POST'])
def routeDebugProbeStarLog():
	jsonData = request.get_json()
	tid = tasks.probeStarLog.delay(jsonData)
	returnObject = {}
	returnObject['task_id'] = str(tid)
	return json.dumps(returnObject)


@debug.route('/sign', methods=['POST'])
def routeDebugSign():
	try:
		jsonData = request.get_json()
		return util.rsaSign(jsonData['private_key'], jsonData['message']), 200
	except:
		traceback.print_exc()
		return '400', 400

@debug.route('/verify-signature', methods=['POST'])
def routeDebugVerifySignature():
	try:
		jsonData = request.get_json()
		return 'valid' if util.rsaVerify(jsonData['public_key'], jsonData['signature'], jsonData['message']) else 'invalid'
	except:
		traceback.print_exc()
		return '400', 400

@debug.route('/sign-jump', methods=['POST'])
def routeDebugSignJump():
	try:
		jsonData = request.get_json()
		message = util.concatJump(jsonData)
		debug.logger.info(message)
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
	except:
		traceback.print_exc()
		return '400', 400

@debug.route('/verify-jump', methods=['POST'])
def routeDebugVerifyJump():
	try:
		jsonData = request.get_json()
		return 'valid' if util.rsaVerifyJump(jsonData) else 'invalid'
	except:
		traceback.print_exc()
		return '400', 400

@debug.route('/unpack-difficulty', methods=['POST'])
def routeDebugUnpackDifficulty():
	try:
		jsonData = request.get_json()
		return util.unpackBits(int(jsonData['difficulty'])), 200
	except:
		traceback.print_exc()
		return '400', 400

@debug.route('/unpack-hex-difficulty', methods=['POST'])
def routeDebugUnpackHexDifficulty():
	try:
		jsonData = request.get_json()
		return util.unpackBits(util.difficultyFromHex(jsonData['hex_difficulty'])), 200
	except:
		traceback.print_exc()
		return '400', 400

@debug.route('/difficulty-change', methods=['POST'])
def routeDebugDifficultyChange():
	try:
		jsonData = request.get_json()
		return str(util.calculateDifficulty(jsonData['difficulty'], jsonData['duration'])), 200
	except:
		traceback.print_exc()
		return '400', 400

@debug.route('/target-to-difficulty', methods=['POST'])
def routeDebugTargetToDifficulty():
	try:
		jsonData = request.get_json()
		return str(util.difficultyFromTarget(jsonData['target'])), 200
	except:
		traceback.print_exc()
		return '400', 400