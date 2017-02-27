import os
import hashlib
import re
import binascii
import traceback
import time
from M2Crypto import BIO, RSA

difficultyFudge = int(os.getenv('DIFFICULTY_FUDGE', 0))

if not 0 <= difficultyFudge <= 8:
	raise ValueError('DIFFICULTY_FUDGE must be a value from 0 to 8 (inclusive)')

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

def verifyFieldIsSha256(sha):
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
def unpackBits(difficulty):
	if not isinstance(difficulty, int):
		raise TypeError('difficulty is not int')
	sha = difficultyToHex(difficulty)
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