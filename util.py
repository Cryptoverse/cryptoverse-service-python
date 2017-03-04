import os
import hashlib
import re
import binascii
import traceback
import time
from M2Crypto import BIO, RSA
from app import app

difficultyFudge = int(os.getenv('DIFFICULTY_FUDGE', 0))
difficultyInterval = int(os.getenv('DIFFICULTY_INTERVAL', 10080))
difficultyDuration = int(os.getenv('DIFFICULTY_DURATION', 160))
difficultyTotalDuration = difficultyDuration * difficultyInterval
maximumTarget = '00000000ffffffffffffffffffffffffffffffffffffffffffffffffffffffff'

if not 0 <= difficultyFudge <= 8:
	raise ValueError('DIFFICULTY_FUDGE must be a value from 0 to 8 (inclusive)')
elif 0 < difficultyFudge:
	prefix = maximumTarget[difficultyFudge:]
	suffix = maximumTarget[:difficultyFudge]
	maximumTarget = prefix + suffix

def isFirstStarLog(previous_hash):
	return previous_hash == '0000000000000000000000000000000000000000000000000000000000000000'

# Returns the Sha256 hash of the provided string, or the hash of nothing if None is passed.
def sha256(text):
	return hashlib.sha256('' if text is None else text).hexdigest()

# Takes the integer format of difficulty and returns a string with its hex representation, sans the leading 0x.
def difficultyToHex(intDifficulty):
	return hex(intDifficulty)[2:]

# Takes a hex string of difficulty, missing the 0x, and returns the integer from of difficulty.
def difficultyFromHex(hexDifficulty):
	return int(hexDifficulty, 16)

# Takes a stripped hex target, without the leading 0x, and returns the stripped hex bit difficulty.
def difficultyFromTarget(hexTarget):
	stripped = hexTarget.lstrip('0')

	# If we stripped too many zeros, add one back.
	if len(stripped) % 2 == 0:
		stripped = '0' + stripped
	
	count = len(stripped) / 2
	stripped = stripped[:6]
	
	# If we're past the max value allowed for the mantissa, truncate it further and increase the exponent.
	if 0x7fffff < int(stripped, 16):
		stripped = '00' + stripped[0:4]
		count += 1
	
	return hex(count)[2:] + stripped

# Checks if it's time to recalculate difficulty.
def isDifficultyChanging(height):
	return (height % difficultyInterval) == 0

# Takes the packed integer difficulty and the duration of the last interval to calculate the new difficulty.
def calculateDifficulty(intDifficulty, duration):
	if duration < difficultyTotalDuration / 4:
		duration = difficultyTotalDuration / 4
	elif duration > difficultyTotalDuration * 4:
		duration = difficultyTotalDuration * 4

	limit = long(maximumTarget, 16)
	result = long(unpackBits(intDifficulty), 16)
	result *= duration
	result /= difficultyTotalDuration

	if limit < result:
		result = limit
	
	return difficultyFromTarget(hex(result)[2:])

def verifyFieldIsSha256(sha):
	''' Verifies a string is a possible Sha256 hash.
	Args:
		sha (str): Hash to test.
	Returns:
		bool: True for success, False otherwise.
	'''
	return re.match(r'^[A-Fa-f0-9]{64}$', sha)

def concatStarLogHeader(jsonStarLog):
	return '%s%s%s%s%s%s' % (jsonStarLog['version'], jsonStarLog['previous_hash'], jsonStarLog['difficulty'], jsonStarLog['nonce'], jsonStarLog['time'], jsonStarLog['state_hash'])

def verifyLogHeader(jsonStarLog):
	return jsonStarLog['log_header'] == concatStarLogHeader(jsonStarLog)

def verifySha256(sha, text):
	return sha == sha256(text)

def concatJump(jump):
	return '%s%s%s%s%s'%(jump['fleet'], jump['key'], jump['origin'], jump['destination'], jump['count'])

def verifyJump(jump):
	hashed_header = sha256(concatJump(jump))
	return verifySignature(str(formatPublicKey(jump['fleet'])), str(jump['signature']), str(hashed_header))

def formatPublicKey(strippedPublicKey):
	return '-----BEGIN PUBLIC KEY-----\n%s\n-----END PUBLIC KEY-----'%(strippedPublicKey)

def verifySignature(publicKey, signature, message):
	try:
		publicRsa = RSA.load_pub_key_bio(BIO.MemoryBuffer(publicKey))
		return publicRsa.verify(bytes(message), binascii.unhexlify(bytearray(signature)), 'sha256') == 1
	except:
		return False

def signHash(privateKey, message):
	privateRsa = RSA.load_key_bio(BIO.MemoryBuffer(privateKey))
	hashed = sha256(message)
	signature = privateRsa.sign(hashed, 'sha256')
	return binascii.hexlify(bytearray(signature))

def hashStarLog(jsonStarLog):
	jsonStarLog['state_hash'] = hashState(jsonStarLog['state'])
	jsonStarLog['log_header'] = concatStarLogHeader(jsonStarLog)
	jsonStarLog['hash'] = sha256(jsonStarLog['log_header'])
	return jsonStarLog

def hashState(state):
	concat = state['fleet']
	for jump in state['jumps']:
		concat += jump['signature']
	for starSystem in state['star_systems']:
		concat += starSystem['hash']
		for deployment in starSystem['deployments']:
			concat += deployment['fleet']
			concat += str(deployment['count'])
	return sha256(concat)

# Take a integer representation of difficulty and return a target hash.
def unpackBits(intDifficulty):
	if not isinstance(intDifficulty, int):
		raise TypeError('difficulty is not int')
	sha = difficultyToHex(intDifficulty)
	digitCount = int(sha[:2], 16)

	if digitCount == 0:
		digitCount = 3

	digits = []
	if digitCount == 29:
		digits = [ sha[4:6], sha[6:8] ]
	else:
		digits = [ sha[2:4], sha[4:6], sha[6:8] ]

	digitCount = min(digitCount, 28)
	significantCount = len(digits)

	leadingPadding = 28 - digitCount
	trailingPadding = 28 - (leadingPadding + significantCount)

	base256 = ''

	for i in range(0, leadingPadding + 4):
		base256 += '00'
	for i in range(0, significantCount):
		base256 += digits[i]
	for i in range(0, trailingPadding):
		base256 += '00'
	
	if 0 < difficultyFudge:
		base256 = base256[difficultyFudge:] + base256[:difficultyFudge]
	return base256

# Takes the integer form of difficulty and verifies that the hash is less than it.
def verifyDifficulty(difficulty, sha):
	if not isinstance(difficulty, int):
		raise TypeError('difficulty is not int')
	if not verifyFieldIsSha256(sha):
		raise ValueError('hash is invalid')

	mask = unpackBits(difficulty).rstrip('0')
	significant = sha[:len(mask)]

	try:
		return int(significant, 16) < int(mask, 16)
	except:
		traceback.print_exc()
		return False

# Someone always gets GMT instead of UTC, so use this.
def getTime():
	return int(time.time())