import re
import binascii
import traceback
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key
import util

def fieldIsSha256(sha):
	'''Verifies a string is a possible Sha256 hash.

	Args:
		sha (str): Hash to verify.

	Returns:
		bool: True for success, False otherwise.
	'''
	return re.match(r'^[A-Fa-f0-9]{64}$', sha)

def rsa(publicKey, signature, message):
	'''Verifies an Rsa signature.
	Args:
		publicKey (str): Public key with BEGIN and END sections.
		signature (str): Hex value of the signature with its leading 0x stripped.
		message (str): Message that was signed, unhashed.

	Returns:
		bool: True if the signature is valid, False otherwise.
	'''
	try:
		publicRsa = load_pem_public_key(bytes(publicKey), backend=default_backend())
		hashed = util.sha256(message)
		publicRsa.verify(
			binascii.unhexlify(signature),
			hashed,
			padding.PSS(
				mgf=padding.MGF1(hashes.SHA256()),
				salt_length=padding.PSS.MAX_LENGTH
			),
			hashes.SHA256()
		)
		return True
	except InvalidSignature:
		return False

def sha256(sha, message):
	'''Verifies the hash matches the Sha256'd message.

	Args:
		sha (str): A Sha256 hash result.
		message (str): Message to hash and compare to.
	
	Returns:
		bool: True if the hash matches the hashed message, False otherwies.
	'''
	return sha == util.sha256(message)

def logHeader(starLog):
	'''Verifies the header of this log matches the provided one.

	Args:
		starLog (dict): Target.

	Returns:
		bool: True if there is a match, False otherwise.
	'''
	return starLog['log_header'] == util.concatStarLogHeader(starLog)

def jumpRsa(jump):
	'''Verifies the Rsa signature of the provided jump json.

	Args:
		jump (dict): Jump to validate.

	Returns:
		bool: True if the jump is properly signed, False otherwise.
	'''
	return rsa(util.expandRsaPublicKey(jump['fleet']), jump['signature'], util.concatJump(jump))

def difficulty(packed, sha):
	'''Takes the integer form of difficulty and verifies that the hash is less than it.

	Args:
		packed (int): Packed target difficulty the provided Sha256 hash must meet.
		sha (str): Hex target to test, stripped of its leading 0x.

	Returns:
		bool: True if the provided Sha256 hash is less than target specified by the packed difficulty.
	'''
	if not isinstance(packed, (int, long)):
		raise TypeError('difficulty is not an int')
	if not fieldIsSha256(sha):
		raise ValueError('hash is invalid')

	mask = util.unpackBits(packed).rstrip('0')
	significant = sha[:len(mask)]
	try:
		return int(significant, 16) < int(mask, 16)
	except:
		traceback.print_exc()
		return False