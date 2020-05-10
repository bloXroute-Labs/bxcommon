import struct
from collections import namedtuple
from typing import List, Union

from bxcommon import constants
from bxcommon.utils.crypto import SHA256_HASH_LEN
from bxcommon.utils.object_hash import Sha256Hash
from bxutils import logging

logger = logging.get_logger(__name__)
TxContentShortIdsV6 = namedtuple("TxContentAndShortIds", ["tx_hash", "tx_content", "short_ids"])


def get_serialized_tx_content_short_ids_bytes_len(tx_content_short_ids: TxContentShortIdsV6) -> int:
    """
    Calculates length of tx content and short ids serialized into bytes

    :param tx_content_short_ids: transaction content and short ids
    :return: length of serialized bytes = tx_hash_size + tx_content_size + len(tx_content) + expiration_time_size
             + short_ids_count + short_ids_count * short_id_size
    """
    short_ids_count = 0
    if tx_content_short_ids.short_ids is not None:
        short_ids_count = len(tx_content_short_ids.short_ids)

    tx_content_size = 0
    if tx_content_short_ids.tx_content is not None:
        tx_content_size = len(tx_content_short_ids.tx_content)

    return SHA256_HASH_LEN + constants.UL_INT_SIZE_IN_BYTES + tx_content_size + constants.UL_INT_SIZE_IN_BYTES + \
        constants.UL_SHORT_SIZE_IN_BYTES + short_ids_count * constants.SID_LEN


def get_serialized_txs_content_short_ids_bytes_len(txs_content_short_ids: List[TxContentShortIdsV6]) -> int:
    return sum([get_serialized_tx_content_short_ids_bytes_len(tx) for tx in txs_content_short_ids])


def serialize_txs_content_short_ids_into_bytes(
    txs_content_short_ids: List[TxContentShortIdsV6], network_num: int
) -> bytearray:
    """
    Serializes list of txs content and short ids into bytes
    :param txs_content_short_ids: list of tuple txs content and short ids
    :param network_num: tx's network number
    :return: bytearray with serialized bytes
    """

    buffer = bytearray(get_serialized_txs_content_short_ids_bytes_len(txs_content_short_ids))
    off = 0
    for tx_content_short_ids in txs_content_short_ids:
        if tx_content_short_ids.tx_content is not None and constants.NULL_TX_SID not in tx_content_short_ids.short_ids:
            buffer[off: off + SHA256_HASH_LEN] = tx_content_short_ids.tx_hash
            off += SHA256_HASH_LEN

            struct.pack_into("<L", buffer, off, len(tx_content_short_ids.tx_content))
            off += constants.UL_INT_SIZE_IN_BYTES
            buffer[off: off + len(tx_content_short_ids.tx_content)] = tx_content_short_ids.tx_content
            off += len(tx_content_short_ids.tx_content)

            # expiration date
            struct.pack_into("<L", buffer, off, 0)
            off += constants.UL_INT_SIZE_IN_BYTES

            struct.pack_into("<H", buffer, off, len(tx_content_short_ids.short_ids))
            off += constants.UL_SHORT_SIZE_IN_BYTES

            for short_id in tx_content_short_ids.short_ids:
                struct.pack_into("<L", buffer, off, short_id)
                off += constants.UL_INT_SIZE_IN_BYTES


        else:
            logger.debug(
                "Transaction {} in network {} is missing either content or short ids. short id is None: {}, "
                "tx content is None: {}", tx_content_short_ids.tx_hash, network_num,
                tx_content_short_ids.short_ids is None, tx_content_short_ids.tx_content is None
            )

    return buffer


def deserialize_txs_content_short_ids_from_buffer(
    buffer: Union[bytearray, memoryview], offset: int, tx_count: int
) -> List[TxContentShortIdsV6]:
    """
    Deserialize list of txs content short ids from buffer

    :param buffer: buffer containing serialized txs content short ids bytes
    :param offset: offset in a buffer where serialized txs content short ids begin
    :param tx_count: how many txs to deserialize
    :return: list of txs content short ids
    """

    txs_content_short_ids: List[TxContentShortIdsV6] = []
    for _ in range(tx_count):
        tx_hash = Sha256Hash(buffer[offset:offset + SHA256_HASH_LEN])
        offset = offset + SHA256_HASH_LEN
        tx_content_size, = struct.unpack_from("<L", buffer, offset)
        offset += constants.UL_INT_SIZE_IN_BYTES
        tx_content = buffer[offset: offset + tx_content_size]
        offset += tx_content_size
        offset += constants.UL_INT_SIZE_IN_BYTES
        short_ids_count, = struct.unpack_from("<H", buffer, offset)
        offset += constants.UL_SHORT_SIZE_IN_BYTES

        short_ids = []
        for _ in range(short_ids_count):
            short_id, = struct.unpack_from("<L", buffer, offset)
            short_ids.append(short_id)
            offset += constants.UL_INT_SIZE_IN_BYTES
        txs_content_short_ids.append(TxContentShortIdsV6(tx_hash, tx_content, short_ids))

    return txs_content_short_ids
