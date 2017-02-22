from __future__ import print_function
from M2Crypto import BIO, RSA
import hashlib
import sys
import re
import hashlib
import binascii

def isFirstStarLog(previous_hash):
	return previous_hash == "0000000000000000000000000000000000000000000000000000000000000000"

def verifyFieldIsHash(hash):
	return re.match(r'^[A-Fa-f0-9]{64}$', hash)

def verifyLogHeader(log_header, version, previous_hash, difficulty, nonce, time, state_hash):
	return log_header == "%s%s%s%s%s%s" % (version, previous_hash, difficulty, nonce, time, state_hash)

def verifyHash(hash, text):
	return hash == hashlib.sha256(text).hexdigest()

def verifyJumpSignatures(jumps):
	for jump in jumps:
		hashed_header = hashlib.sha256("%s%s%s%s%s"%(jump['fleet'], jump['key'], jump['origin'], jump['destination'], jump['count'])).hexdigest()
		print(verifySignature(str(formatPublicKey(jump['fleet'])), str(jump['signature']), str(hashed_header)), file=sys.stderr)

def formatPublicKey(strippedPublicKey):
	return "-----BEGIN PUBLIC KEY-----\n%s\n-----END PUBLIC KEY-----"%(strippedPublicKey)

def verifySignature(pubkey, signature, message):
	try:
		pubRsa = RSA.load_pub_key_bio(BIO.MemoryBuffer(pubkey))
		verify = pubRsa.verify(bytes(message), binascii.unhexlify(bytearray(signature)), 'sha256')
		return True
	except:
		return False
