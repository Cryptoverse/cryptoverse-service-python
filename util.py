from M2Crypto import BIO, RSA
from app import app
import hashlib
import sys
import re
import binascii

def isFirstStarLog(previous_hash):
	return previous_hash == "0000000000000000000000000000000000000000000000000000000000000000"

def sha256(text):
	return hashlib.sha256(text).hexdigest()

def verifyFieldIsHash(hash):
	return re.match(r'^[A-Fa-f0-9]{64}$', hash)

def concatLogHeader(version, previous_hash, difficulty, nonce, time, state_hash):
	return "%s%s%s%s%s%s" % (version, previous_hash, difficulty, nonce, time, state_hash)

def verifyLogHeader(log_header, version, previous_hash, difficulty, nonce, time, state_hash):
	return log_header == concatLogHeader(version, previous_hash, difficulty, nonce, time, state_hash)

def verifyHash(hash, text):
	return hash == sha256(text)

def concatJump(jump):
	return "%s%s%s%s%s"%(jump['fleet'], jump['key'], jump['origin'], jump['destination'], jump['count'])

def verifyJump(jump):
	hashed_header = sha256(concatJump(jump))
	return verifySignature(str(formatPublicKey(jump['fleet'])), str(jump['signature']), str(hashed_header))	

def formatPublicKey(strippedPublicKey):
	return "-----BEGIN PUBLIC KEY-----\n%s\n-----END PUBLIC KEY-----"%(strippedPublicKey)

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

def hashLog(log):
	log['state_hash'] = hashState(log['state'])
	log['log_header'] = concatLogHeader(log['version'], log['previous_hash'], log['difficulty'], log['nonce'], log['time'], log['state_hash'])
	log['hash'] = sha256(log['log_header'])
	return log

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

# Take a hex bits representation of difficulty and return a target hash
def unpackBits(hex):
	if not len(hex) == 8:
		raise ValueError("hex string must have 8 characters")

	digitCount = int(hex[:2], 16)

	if digitCount == 0:
		digitCount = 3

	digits = []
	if digitCount == 29:
		digits = [ hex[4:6], hex[6:8] ]
	else:
		digits = [ hex[2:4], hex[4:6], hex[6:8] ]
	
	digitCount = min(digitCount, 28)
	significantCount = len(digits)

	leadingPadding = 28 - digitCount
	trailingPadding = 28 - (leadingPadding + significantCount)

	base256 = ""

	for i in range(0, leadingPadding + 4):
		base256 += "00"
	for i in range(0, significantCount):
		base256 += digits[i]
	for i in range(0, trailingPadding):
		base256 += "00"

	return base256
