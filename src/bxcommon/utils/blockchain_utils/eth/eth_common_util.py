from typing import Union, Tuple, Optional

from Crypto.Hash import keccak

from bxcommon.exceptions import ParseError
from bxcommon.messages.bloxroute.tx_message import TxMessage
from bxcommon.models.quota_type_model import QuotaType
from bxcommon.utils.blockchain_utils.eth import eth_common_constants
from bxcommon.utils.object_hash import Sha256Hash

# pylint: disable=invalid-name


def raw_tx_to_bx_tx(
    txs_bytes: Union[bytearray, memoryview],
    tx_start_index: int,
    network_num: int,
    quota_type: Optional[QuotaType] = None
) -> Tuple[TxMessage, int, int]:
    if isinstance(txs_bytes, bytearray):
        txs_bytes = memoryview(txs_bytes)
    _, tx_item_length, tx_item_start = consume_length_prefix(txs_bytes, tx_start_index)
    tx_bytes = txs_bytes[tx_start_index:tx_item_start + tx_item_length]
    tx_hash_bytes = keccak_hash(tx_bytes)
    msg_hash = Sha256Hash(tx_hash_bytes)
    bx_tx = TxMessage(message_hash=msg_hash, network_num=network_num, tx_val=tx_bytes, quota_type=quota_type)
    return bx_tx, tx_item_length, tx_item_start


def keccak_hash(string):
    """
    Ethereum Crypto Utils:
    Calculates SHA3 hash of the string

    :param string: string to calculate hash from
    :return: SHA3 hash
    """

    if not string:
        raise ValueError("Input is required")

    k_hash = keccak.new(digest_bits=eth_common_constants.SHA3_LEN_BITS, data=string)
    return k_hash.digest()


def safe_ord(c):
    """
    Ethereum RLP Utils:
    Returns an integer representing the Unicode code point of the character or int if int argument is passed

    :param c: character or integer
    :return: integer representing the Unicode code point of the character or int if int argument is passed
    """

    if isinstance(c, int):
        return c
    else:
        return ord(c)


def big_endian_to_int(value):
    """
    Ethereum RLP Utils:
    Convert big endian to int

    :param value: big ending value
    :return: int value
    """

    return int.from_bytes(value, byteorder="big")


def int_to_big_endian(value: int) -> bytes:
    return value.to_bytes((value.bit_length() + 7) // 8 or 1, byteorder="big")


def consume_length_prefix(rlp, start):
    """
    Ethereum RLP Utils:
    Read a length prefix from an RLP string.

    :param rlp: the rlp string to read from
    :param start: the position at which to start reading
    :returns: a tuple ``(type, length, end)``, where ``type`` is either ``str``
              or ``list`` depending on the type of the following payload,
              ``length`` is the length of the payload in bytes, and ``end`` is
              the position of the first payload byte in the rlp string
    """
    if not isinstance(rlp, memoryview):
        raise TypeError("Only memoryview is allowed for RLP content for best performance. Type provided was: {}"
                        .format(type(rlp)))

    if start is None:
        raise ValueError("Argument start is required")

    b0 = safe_ord(rlp[start])
    if b0 < 128:  # single byte
        return (str, 1, start)
    elif b0 < 128 + 56:  # short string
        if b0 - 128 == 1 and safe_ord(rlp[start + 1]) < 128:
            raise ParseError("Encoded as short string although single byte was possible")
        return (str, b0 - 128, start + 1)
    elif b0 < 192:  # long string
        ll = b0 - 128 - 56 + 1
        if rlp[start + 1:start + 2] == b"\x00":
            raise ParseError("Length starts with zero bytes")
        l = big_endian_to_int(rlp[start + 1:start + 1 + ll])
        if l < 56:
            raise ParseError("Long string prefix used for short string")
        return (str, l, start + 1 + ll)
    elif b0 < 192 + 56:  # short list
        return (list, b0 - 192, start + 1)
    else:  # long list
        ll = b0 - 192 - 56 + 1
        if rlp[start + 1:start + 2] == b"\x00":
            raise ParseError("Length starts with zero bytes")
        l = big_endian_to_int(rlp[start + 1:start + 1 + ll])
        if l < 56:
            raise ParseError("Long list prefix used for short list")
        return (list, l, start + 1 + ll)
