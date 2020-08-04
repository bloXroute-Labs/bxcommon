import struct
from typing import List, Tuple, Union

from bxcommon import constants
from bxcommon.models.transaction_info import TransactionInfo
from bxcommon.utils import crypto
from bxcommon.utils.object_hash import Sha256Hash


def get_serialized_length(transactions_info: List[TransactionInfo]) -> int:
    message_size = constants.UL_INT_SIZE_IN_BYTES + len(transactions_info) * (
        constants.UL_INT_SIZE_IN_BYTES
        + crypto.SHA256_HASH_LEN
        + constants.UL_INT_SIZE_IN_BYTES
    )

    for tx in transactions_info:
        tx_contents = tx.contents
        assert tx_contents is not None
        message_size += len(tx_contents)

    return message_size


def serialize_transactions_info_to_buffer(txs_info: List[TransactionInfo], buffer: bytearray,
                                          offset: int = 0) -> int:
    struct.pack_into("<L", buffer, offset, len(txs_info))
    offset += constants.UL_INT_SIZE_IN_BYTES

    for tx_info in txs_info:
        struct.pack_into("<L", buffer, offset, tx_info.short_id)
        offset += constants.UL_INT_SIZE_IN_BYTES

        tx_hash = tx_info.hash
        assert tx_hash is not None
        assert tx_hash.binary is not None
        buffer[offset:offset + crypto.SHA256_HASH_LEN] = tx_hash.binary
        offset += crypto.SHA256_HASH_LEN

        tx_contents = tx_info.contents
        assert tx_contents is not None
        struct.pack_into("<L", buffer, offset, len(tx_contents))
        offset += constants.UL_INT_SIZE_IN_BYTES

        buffer[offset:offset + len(tx_contents)] = tx_contents
        offset += len(tx_contents)

    return offset


def serialize_transactions_info(transactions_info: List[TransactionInfo]) -> bytearray:
    serialized_bytes = bytearray(get_serialized_length(transactions_info))
    serialize_transactions_info_to_buffer(transactions_info, serialized_bytes, 0)
    return serialized_bytes


def deserialize_transactions_info_from_buffer(
    buffer: Union[bytearray, memoryview],
    offset: int = 0
) -> Tuple[List[TransactionInfo], int]:
    txs = []

    txs_count, = struct.unpack_from("<L", buffer, offset)
    offset += constants.UL_INT_SIZE_IN_BYTES

    for _ in range(txs_count):
        tx_sid, = struct.unpack_from("<L", buffer, offset)
        offset += constants.UL_INT_SIZE_IN_BYTES

        tx_hash = Sha256Hash(buffer[offset:offset + crypto.SHA256_HASH_LEN])
        offset += crypto.SHA256_HASH_LEN

        tx_size, = struct.unpack_from("<L", buffer, offset)
        offset += constants.UL_INT_SIZE_IN_BYTES

        tx = buffer[offset:offset + tx_size]
        offset += tx_size

        txs.append(TransactionInfo(tx_hash, tx, tx_sid))

    return txs, offset


def deserialize_transactions_info(buffer: Union[bytearray, memoryview]) -> List[TransactionInfo]:
    transactions_info, _ = deserialize_transactions_info_from_buffer(buffer, 0)
    return transactions_info
