from typing import Union, Tuple, Optional

from Crypto.Hash import keccak

from bxcommon.messages.bloxroute.tx_message import TxMessage
from bxcommon.models.quota_type_model import QuotaType
from bxcommon.utils.blockchain_utils.eth import eth_common_constants, rlp_utils
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



def raw_tx_gas_price(tx_bytes: memoryview, tx_start_index: int) -> int:
    _, tx_item_length, tx_item_start = rlp_utils.consume_length_prefix(tx_bytes, tx_start_index)
    tx_bytes = tx_bytes[tx_item_start:tx_item_start + tx_item_length]

    # gas_price is the second field, need to skip the first field (nonce)
    _, nonce_item_length, nonce_item_start = rlp_utils.consume_length_prefix(tx_bytes, 0)

    gas_price, _ = rlp_utils.decode_int(tx_bytes, nonce_item_start + nonce_item_length)
    return gas_price


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


def int_to_big_endian(value: int) -> bytes:
    return value.to_bytes((value.bit_length() + 7) // 8 or 1, byteorder="big")
