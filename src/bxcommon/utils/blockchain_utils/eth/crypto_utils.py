import hashlib
import os
import struct

import bitcoin
from Crypto.Hash import keccak
from coincurve import PrivateKey, PublicKey

from bxcommon.utils import convert
from bxcommon.utils.blockchain_utils.eth import eth_common_utils, eth_common_constants
from bxcommon.utils.blockchain_utils.eth import rlp_utils


def sign(msg, private_key):
    """
    Signs message using private key
    """

    if not msg:
        raise ValueError("Message is required")

    if len(private_key) != eth_common_constants.PRIVATE_KEY_LEN:
        raise ValueError("Private key is expected of len {0} but was {1}"
                         .format(eth_common_constants.PRIVATE_KEY_LEN, len(private_key)))

    new_private_key = PrivateKey(private_key)
    return new_private_key.sign_recoverable(msg, hasher=None)


def get_sha3_calculator(input_bytes):
    """
    Returns object that can be used to calculate sha3 hash
    :param input_bytes: input bytes
    :return: object that can calculate sha3 256 hash
    """

    if input_bytes is None:
        raise ValueError("Input is required")

    return keccak.new(digest_bits=eth_common_constants.SHA3_LEN_BITS, update_after_digest=True, data=input_bytes)


def recover_public_key(message, signature, hasher=None):
    """
    Recovers public key from signed message
    :param message: message
    :param signature: signature
    :param hasher: hash function to use on message (usually sha256 or keccak_hash)
    :return: public key
    """

    if len(signature) != eth_common_constants.SIGNATURE_LEN:
        raise ValueError("Expected signature len of {0} but was {1}"
                         .format(eth_common_constants.SIGNATURE_LEN, len(signature)))

    public_key = PublicKey.from_signature_and_message(signature, message, hasher=hasher)
    return public_key.format(compressed=False)[1:]


def verify_signature(pubkey, signature, message):
    """
    Verifies signature
    :param pubkey: signing public key
    :param signature: message signature
    :param message: signature
    :return: returns True if signature is valid, False otherwise
    """

    if len(pubkey) != eth_common_constants.PUBLIC_KEY_LEN:
        raise ValueError("Pubkey is expected of len {0} but was {1}"
                         .format(eth_common_constants.PUBLIC_KEY_LEN, len(pubkey)))

    if len(signature) != eth_common_constants.SIGNATURE_LEN:
        raise ValueError("Signature is expected of len {0} but was {1}"
                         .format(eth_common_constants.PUBLIC_KEY_LEN, len(signature)))

    if not message:
        raise ValueError("Message is required")

    public_key = PublicKey.from_signature_and_message(signature, message, hasher=None)
    return public_key.format(compressed=False) == b"\04" + pubkey


def encode_signature(tx_v: int, tx_r: int, tx_s: int) -> bytes:
    """
    Calculates byte representation of ECC signature from parameters
    :param tx_v:
    :param tx_r:
    :param tx_s:
    :return: bytes of ECC signature
    """
    if tx_v > eth_common_constants.EIP155_CHAIN_ID_OFFSET:
        if tx_v % 2 == 0:
            tx_v = 28
        else:
            tx_v = 27

    if tx_v not in (27, 28):
        raise ValueError("v is expected to be int or long in range (27, 28)")

    return encode_signature_y_parity(tx_v - 27, tx_r, tx_s)


def encode_signature_y_parity(y_parity: int, tx_r: int, tx_s: int) -> bytes:
    v_bytes = rlp_utils.ascii_chr(y_parity)
    # pyre-fixme[16]: Module `bitcoin` has no attribute `encode`.
    # pyre-fixme[16]: Module `bitcoin` has no attribute `encode`.
    r_bytes, s_bytes = bitcoin.encode(tx_r, 256), bitcoin.encode(tx_s, 256)
    return _left_0_pad_32(r_bytes) + _left_0_pad_32(s_bytes) + v_bytes


def decode_signature(sig):
    """
    Decodes coordinates from ECC signature bytes
    :param sig: signature bytes
    :return: ECC signature parameters
    """

    if not sig:
        raise ValueError("Signature is required")

    return rlp_utils.safe_ord(sig[64]) + 27, bitcoin.decode(sig[0:32], 256), bitcoin.decode(sig[32:64], 256)


def make_private_key(seed):
    """
    Generates ECC private using provided seed value
    :param seed: seed used to generate ECC private key
    :return: ECC private key
    """

    if not seed:
        raise ValueError("Seed is required")

    return eth_common_utils.keccak_hash(seed)


def generate_random_private_key_hex_str():
    """
    Generate hex string of random ECC private key
    :return: ECC private key hex string
    """

    # seed can be any random bytes of any length
    random_seed = os.urandom(100)
    private_key_bytes = make_private_key(random_seed)
    return convert.bytes_to_hex(private_key_bytes)


def private_to_public_key(raw_private_key):
    """
    Calculates public key for private key
    :param raw_private_key: ECC private key
    :return: public key
    """

    if len(raw_private_key) != eth_common_constants.PRIVATE_KEY_LEN:
        raise ValueError("Private key is expected of len {0} but was {1}"
                         .format(eth_common_constants.PRIVATE_KEY_LEN, len(raw_private_key)))

    raw_pubkey = bitcoin.encode_pubkey(bitcoin.privtopub(raw_private_key), "bin_electrum")
    assert len(raw_pubkey) == eth_common_constants.PUBLIC_KEY_LEN
    return raw_pubkey


def ecies_kdf(key_material, key_len):
    """
    interop w/go ecies implementation

    for sha3, blocksize is 136 bytes
    for sha256, blocksize is 64 bytes

    NIST SP 800-56a Concatenation Key Derivation Function (see section 5.8.1).

    :param key_material: key material
    :param key_len: key length
    :return: key
    """

    if len(key_material) != eth_common_constants.KEY_MATERIAL_LEN:
        raise ValueError("Key material is expected of len {0} but was {1}"
                         .format(eth_common_constants.KEY_MATERIAL_LEN, len(key_material)))

    if key_len <= 0:
        raise ValueError("Key len is expected to be positive but was {0}".format(key_len))

    empty_bytes = b""
    key = b""
    hash_blocksize = eth_common_constants.BLOCK_HASH_LEN
    reps = ((key_len + 7) * 8) / (hash_blocksize * 8)
    counter = 0
    while counter <= reps:
        counter += 1
        ctx = hashlib.sha256()
        ctx.update(struct.pack(">I", counter))
        ctx.update(key_material)
        ctx.update(empty_bytes)
        key += ctx.digest()
    return key[:key_len]


def string_xor(string_1, string_2):
    """
    Calculates xor of two strings
    :param string_1: string 1
    :param string_2: string 2
    :return: xor of two strings
    """

    if len(string_1) != len(string_2):
        raise ValueError("String must have the same length")

    return b"".join(
        rlp_utils.ascii_chr(rlp_utils.safe_ord(a) ^ rlp_utils.safe_ord(b)) for a, b in zip(string_1, string_2)
    )


def get_padded_len_16(input_bytes):
    """
    Length of bytes if padded to 16
    :param input_bytes: bytes
    :return: padded length
    """

    return input_bytes if input_bytes % eth_common_constants.MSG_PADDING == 0 \
        else input_bytes + eth_common_constants.MSG_PADDING - (input_bytes % eth_common_constants.MSG_PADDING)


def right_0_pad_16(data):
    """
    Pads bytes with 0 on the right to length of 16
    :param data: bytes
    :return: padded bytes
    """

    if len(data) % eth_common_constants.MSG_PADDING:
        data += b"\x00" * (eth_common_constants.MSG_PADDING - len(data) % eth_common_constants.MSG_PADDING)
    return data


def _left_0_pad_32(input_bytes):
    """
    Pads bytes with 0 on the left to length of 32
    :param input_bytes: bytes
    :return: padded bytes
    """

    return b"\x00" * (32 - len(input_bytes)) + input_bytes


def public_key_to_address(public_key_bytes: bytes) -> bytes:
    return eth_common_utils.keccak_hash(memoryview(public_key_bytes))[-20:]
