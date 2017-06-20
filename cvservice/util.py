import hashlib
import binascii
import time
import uuid
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key

def sha256(message):
    """Sha256 hash of message.
    
    Args:
        message (str): Message to hash.
    
    Returns:
        str: Sha256 hash of the provided string, or the hash of nothing if None is passed.
    """
    return hashlib.sha256('' if message is None else message).hexdigest()


def expand_rsa_public_key(shrunk_public_key):
    """Reformats a shrunk Rsa public key.

    Args:
        shrunk_public_key (str): Rsa public key without the BEGIN or END sections.
    
    Returns:
        str: The public key with its BEGIN and END sections reattatched.
    """
    return '-----BEGIN PUBLIC KEY-----\n%s\n-----END PUBLIC KEY-----'%(shrunk_public_key)


def rsa_sign(private_key, message):
    """Signs a message with the provided Rsa private key.

    Args:
        private_key (str): Rsa private key with BEGIN and END sections.
        message (str): Message to be hashed and signed.
    
    Returns:
        str: Hex signature of the message, with its leading 0x stripped.
    """
    private_rsa = load_pem_private_key(bytes(private_key), password=None, backend=default_backend())
    hashed = sha256(message)
    signature = private_rsa.sign(
        hashed,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return binascii.hexlify(bytearray(signature))


def get_unique_key():
    """The sha256 of a unique id.

    Returns:
        str: The sha256 of a unique id.
    """
    return sha256(str(uuid.uuid4()))


def get_time():
    """UTC time in seconds.

    Returns:
        int: The number of seconds since the UTC epoch started.
    """
    return int(time.time())