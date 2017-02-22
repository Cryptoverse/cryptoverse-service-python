from __future__ import print_function
import sys
import re
import hashlib

def isFirstStarLog(previous_hash):
	return previous_hash == "0000000000000000000000000000000000000000000000000000000000000000"

def verifyFieldIsHash(hash):
	return re.match(r'^[A-Fa-f0-9]{64}$', hash)

def verifyLogHeader(log_header, version, previous_hash, difficulty, nonce, time, state_hash):
	return log_header == "%s%s%s%s%s%s" % (version, previous_hash, difficulty, nonce, time, state_hash)

def verifyHash(hash, text):
	return hash == hashlib.sha256(text).hexdigest()
