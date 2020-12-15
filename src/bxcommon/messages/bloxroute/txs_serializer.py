import struct
from typing import NamedTuple, Optional, List, Union

from bxcommon import constants
from bxcommon.models.transaction_flag import TransactionFlag
from bxcommon.utils.crypto import SHA256_HASH_LEN
from bxcommon.utils.object_hash import Sha256Hash
from bxutils import logging

logger = logging.get_logger(__name__)


class TxContentShortIds(NamedTuple):
    tx_hash: Sha256Hash
    tx_content: Optional[Union[bytearray, memoryview]]
    short_ids: List[int]
    short_id_flags: List[TransactionFlag]


def get_serialized_tx_content_short_ids_bytes_len(tx_content_short_ids: TxContentShortIds) -> int:
    """
    Calculates length of tx content and short ids serialized into bytes

    :param tx_content_short_ids: transaction content and short ids
    :return: length of serialized bytes = tx_hash_size + tx_content_size + len(tx_content)
             + expiration_time_size + short_ids_count + short_ids_count * short_id_size
    """
    short_ids_count = 0
    if tx_content_short_ids.short_ids is not None:
        short_ids_count = len(tx_content_short_ids.short_ids)

    tx_content_size = 0
    if tx_content_short_ids.tx_content is not None:
        # pyre-fixme[6]: Expected `Sized` for 1st param but got
        #  `Optional[Union[bytearray, memoryview]]`.
        tx_content_size = len(tx_content_short_ids.tx_content)

    return SHA256_HASH_LEN + constants.UL_INT_SIZE_IN_BYTES + tx_content_size + constants.UL_INT_SIZE_IN_BYTES + \
        constants.UL_SHORT_SIZE_IN_BYTES + (constants.SID_LEN + constants.TRANSACTION_FLAG_LEN) * short_ids_count


def get_serialized_txs_content_short_ids_bytes_len(txs_content_short_ids: List[TxContentShortIds]) -> int:
    return sum([get_serialized_tx_content_short_ids_bytes_len(tx) for tx in txs_content_short_ids])


def serialize_txs_content_short_ids_into_bytes(
    txs_content_short_ids: List[TxContentShortIds], network_num: int
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
            buffer[off: off + SHA256_HASH_LEN] = tx_content_short_ids.tx_hash.binary
            off += SHA256_HASH_LEN

            # pyre-fixme[6]: Expected `Sized` for 1st param but got
            #  `Optional[Union[bytearray, memoryview]]`.
            struct.pack_into("<L", buffer, off, len(tx_content_short_ids.tx_content))
            off += constants.UL_INT_SIZE_IN_BYTES
            # pyre-fixme[6]: Expected `Sized` for 1st param but got
            #  `Optional[Union[bytearray, memoryview]]`.
            # pyre-fixme[6]: Expected `Union[typing.Iterable[int], bytes]` for 2nd
            #  param but got `Optional[Union[bytearray, memoryview]]`.
            buffer[off: off + len(tx_content_short_ids.tx_content)] = tx_content_short_ids.tx_content
            # pyre-fixme[6]: Expected `Sized` for 1st param but got
            #  `Optional[Union[bytearray, memoryview]]`.
            off += len(tx_content_short_ids.tx_content)

            # expiration date
            struct.pack_into("<L", buffer, off, 0)
            off += constants.UL_INT_SIZE_IN_BYTES

            struct.pack_into("<H", buffer, off, len(tx_content_short_ids.short_ids))
            off += constants.UL_SHORT_SIZE_IN_BYTES

            for short_id in tx_content_short_ids.short_ids:
                struct.pack_into("<L", buffer, off, short_id)
                off += constants.SID_LEN

            # we pass a transaction flags for each short id provided
            # we pass an array of flags following the array of short ids, in matching order
            # we require that transaction flags array to be the same length of the short_ids array,
            # if validation fail, we will pass empty values as the transaction flags,
            # to make backwards compatibility easier.
            assert len(tx_content_short_ids.short_id_flags) == len(tx_content_short_ids.short_ids),\
                "Invalid TransactionFlag Array Provided"
            for short_id_tx_flag in tx_content_short_ids.short_id_flags:
                struct.pack_into("<H", buffer, off, short_id_tx_flag.value)
                off += constants.TRANSACTION_FLAG_LEN

        else:
            logger.debug(
                "Transaction {} in network {} is missing either content or short ids. short id is None: {}, "
                "tx content is None: {}", tx_content_short_ids.tx_hash, network_num,
                tx_content_short_ids.short_ids is None, tx_content_short_ids.tx_content is None
            )

    return buffer


def deserialize_txs_content_short_ids_from_buffer(
    buffer: Union[bytearray, memoryview], offset: int, tx_count: int
) -> List[TxContentShortIds]:
    """
    Deserialize list of txs content short ids from buffer

    :param buffer: buffer containing serialized txs content short ids bytes
    :param offset: offset in a buffer where serialized txs content short ids begin
    :param tx_count: how many txs to deserialize
    :return: list of txs content short ids
    """

    txs_content_short_ids: List[TxContentShortIds] = []
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
        short_id_flags = []
        for _ in range(short_ids_count):
            short_id, = struct.unpack_from("<L", buffer, offset)
            short_ids.append(short_id)
            offset += constants.SID_LEN
        for _ in range(short_ids_count):
            short_id_flag, = struct.unpack_from("<H", buffer, offset)
            short_id_flags.append(TransactionFlag(short_id_flag))
            offset += constants.TRANSACTION_FLAG_LEN
        txs_content_short_ids.append(TxContentShortIds(tx_hash, tx_content, short_ids, short_id_flags))

    return txs_content_short_ids
