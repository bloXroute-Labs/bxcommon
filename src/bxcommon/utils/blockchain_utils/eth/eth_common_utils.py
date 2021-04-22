from typing import Union, Tuple, Optional, Type

from Crypto.Hash import keccak

from bxcommon.messages.bloxroute.tx_message import TxMessage
from bxcommon.messages.eth.serializers.transaction_type import EthTransactionType
from bxcommon.models.transaction_flag import TransactionFlag
from bxcommon.utils.blockchain_utils.eth import eth_common_constants, rlp_utils
from bxcommon.utils.object_hash import Sha256Hash
from bxcommon import constants

import blxr_rlp as rlp


def raw_tx_to_bx_tx(
    tx_bytes: Union[bytearray, memoryview],
    tx_start_index: int,
    network_num: int,
    transaction_flag: Optional[TransactionFlag] = None,
    account_id: str = constants.DECODED_EMPTY_ACCOUNT_ID
) -> Tuple[TxMessage, Type, int, int]:
    if isinstance(tx_bytes, bytearray):
        tx_bytes = memoryview(tx_bytes)
    tx_item_type, tx_item_length, tx_item_start = rlp_utils.consume_length_prefix(tx_bytes, tx_start_index)
    tx_bytes = tx_bytes[tx_start_index:tx_item_start + tx_item_length]

    if tx_item_type == str:
        tx_hash_bytes = keccak_hash(rlp.decode(tx_bytes.tobytes()))
    else:
        tx_hash_bytes = keccak_hash(tx_bytes)
    msg_hash = Sha256Hash(tx_hash_bytes)
    bx_tx = TxMessage(
        message_hash=msg_hash,
        network_num=network_num,
        tx_val=tx_bytes,
        transaction_flag=transaction_flag,
        account_id=account_id
    )
    return bx_tx, tx_item_type, tx_item_length, tx_item_start


def tx_type(tx_bytes: memoryview, tx_start_index: int) -> Tuple[EthTransactionType, memoryview]:
    """
    Reads the transaction type off the top of the memoryview, then normalizes the
    memoryview so that the beginning of the transaction is at the beginning of
    the returned slice.
    """
    transaction_type = EthTransactionType.LEGACY
    first_byte = tx_bytes[tx_start_index]
    if first_byte <= eth_common_constants.MAX_TRANSACTION_TYPE:
        tx_start_index += 1
        try:
            transaction_type = EthTransactionType(first_byte)
        except Exception:
            pass
    return transaction_type, tx_bytes[tx_start_index:]


def raw_tx_gas_price(tx_bytes: memoryview, tx_start_index: int) -> int:
    tx_item_type, tx_item_length, tx_item_start = rlp_utils.consume_length_prefix(tx_bytes, tx_start_index)

    # if transaction is an EIP-2718 envelope, decode the string a second time to
    # get the actual tx item
    if tx_item_type == str:
        tx_bytes = tx_bytes[tx_item_start:]
        tx_start_index = 0
        _, tx_item_length, tx_item_start = rlp_utils.consume_length_prefix(tx_bytes, tx_start_index)

    transaction_type, tx_bytes = tx_type(tx_bytes, tx_start_index)
    _, tx_item_length, tx_item_start = rlp_utils.consume_length_prefix(tx_bytes, 0)

    tx_bytes = tx_bytes[tx_item_start:tx_item_start + tx_item_length]

    offset = 0
    if transaction_type == EthTransactionType.ACCESS_LIST:
        _chain_id, chain_id_length = rlp_utils.decode_int(tx_bytes, offset)
        offset += chain_id_length

        _nonce, nonce_length = rlp_utils.decode_int(tx_bytes, offset)
        offset += nonce_length
    else:
        # gas_price is the second field, need to skip the first field (nonce)
        _nonce, nonce_length = rlp_utils.decode_int(tx_bytes, offset)
        offset += nonce_length

    gas_price, _ = rlp_utils.decode_int(tx_bytes, offset)
    return gas_price


def keccak_hash(body: memoryview) -> bytes:
    """
    Ethereum Crypto Utils:
    Calculates SHA3 hash of the string
    :param body: bytes to calculate hash from
    :return: SHA3 hash
    """

    if not body:
        raise ValueError("Input is required")

    k_hash = keccak.new(digest_bits=eth_common_constants.SHA3_LEN_BITS, data=body)
    return k_hash.digest()


def int_to_big_endian(value: int) -> bytes:
    return value.to_bytes((value.bit_length() + 7) // 8 or 1, byteorder="big")


def block_header_number(full_block_header_bytes: Union[memoryview, bytearray]) -> int:
    _, block_header_len, block_header_start = rlp_utils.consume_length_prefix(full_block_header_bytes, 0)
    block_header_bytes = full_block_header_bytes[block_header_start:block_header_start + block_header_len]
    offset = eth_common_constants.FIXED_LENGTH_FIELD_OFFSET
    _difficulty, difficulty_length = rlp_utils.decode_int(block_header_bytes, offset)
    offset += difficulty_length
    number, _ = rlp_utils.decode_int(block_header_bytes, offset)
    return number


def block_header_difficulty(full_block_header_bytes: Union[memoryview, bytearray]) -> int:
    _, block_header_len, block_header_start = rlp_utils.consume_length_prefix(full_block_header_bytes, 0)
    block_header_bytes = full_block_header_bytes[block_header_start:block_header_start + block_header_len]
    offset = eth_common_constants.FIXED_LENGTH_FIELD_OFFSET
    difficulty, _difficulty_length = rlp_utils.decode_int(block_header_bytes, offset)
    return difficulty
