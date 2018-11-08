from hashlib import sha256

from nacl.secret import SecretBox
from nacl.utils import random

# Length of a SHA256 double hash
SHA256_HASH_LEN = 32
KEY_SIZE = SecretBox.KEY_SIZE


def bitcoin_hash(content):
    return sha256(sha256(content).digest()).digest()


def double_sha256(content):
    return sha256(sha256(content).digest()).digest()


def symmetric_encrypt(content, key=None):
    if not key:
        key = random(KEY_SIZE)
    ciphertext = SecretBox(key).encrypt(content)
    return key, ciphertext


def symmetric_decrypt(key, ciphertext):
    return SecretBox(key).decrypt(ciphertext)
