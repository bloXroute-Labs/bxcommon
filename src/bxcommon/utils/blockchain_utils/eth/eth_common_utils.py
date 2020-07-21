from typing import Union, Tuple, Optional

import rlp
from Crypto.Hash import keccak
from rlp.sedes import List

from bxcommon.messages.bloxroute.tx_message import TxMessage
from bxcommon.messages.eth.serializers.transaction import Transaction
from bxcommon.models.quota_type_model import QuotaType
from bxcommon.models.tx_validation_status import TxValidationStatus
from bxcommon.utils.blockchain_utils.eth import eth_common_constants, crypto_utils, rlp_utils
from bxcommon.utils.object_hash import Sha256Hash


def raw_tx_to_bx_tx(
    tx_bytes: Union[bytearray, memoryview],
    tx_start_index: int,
    network_num: int,
    quota_type: Optional[QuotaType] = None
) -> Tuple[TxMessage, int, int]:
    if isinstance(tx_bytes, bytearray):
        tx_bytes = memoryview(tx_bytes)
    _, tx_item_length, tx_item_start = rlp_utils.consume_length_prefix(tx_bytes, tx_start_index)
    tx_bytes = tx_bytes[tx_start_index:tx_item_start + tx_item_length]
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


def verify_eth_transaction_signature(transaction: Transaction) -> bool:
    """
    checks eth transaction signature
    :param transaction:
    :return: if signature matches public key
    """
    try:
        signature = crypto_utils.encode_signature(transaction.v, transaction.r, transaction.s)
        unsigned_msg = transaction.get_unsigned()
        public_key = crypto_utils.recover_public_key(unsigned_msg, signature, keccak_hash)
        return crypto_utils.verify_signature(public_key, signature, keccak_hash(unsigned_msg))
    except (ValueError, rlp.exceptions.DecodingError):
        return False


def parse_transaction(tx_bytes: memoryview) -> Optional[Transaction]:
    """
    :param tx_bytes: transaction bytes
    :return: if transaction successfully parsed returns None else transaction
    """
    try:
        payload = rlp.decode(bytearray(tx_bytes), strict=False)
        serializers: List = List([serializer for _, serializer in Transaction.fields])
        serializers.deserialize(payload)

        return Transaction(*serializers.deserialize(payload))

    except (ValueError, rlp.exceptions.DecodingError):
        return None


def validate_transaction(tx_bytes: Union[bytearray, memoryview]) -> TxValidationStatus:
    """
    check if transaction is validated - signature is correct and format is valid
    :param tx_bytes:
    :return:
    """
    if isinstance(tx_bytes, bytearray):
        tx_bytes = memoryview(tx_bytes)

    transaction = parse_transaction(tx_bytes)
    if transaction:
        if verify_eth_transaction_signature(transaction):
            return TxValidationStatus.VALID_TX
        else:
            return TxValidationStatus.INVALID_SIGNATURE

    return TxValidationStatus.INVALID_FORMAT
