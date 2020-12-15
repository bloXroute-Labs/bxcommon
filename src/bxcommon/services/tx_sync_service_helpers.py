import struct
import time
from typing import List, Optional, Tuple, Set

from bxcommon import constants
from bxcommon.messages.bloxroute import txs_serializer
from bxcommon.messages.bloxroute.tx_service_sync_txs_message import TxServiceSyncTxsMessage
from bxcommon.messages.bloxroute.txs_serializer import TxContentShortIds
from bxcommon.services.transaction_service import TransactionService, TransactionCacheKeyType
from bxcommon.utils import crypto
from bxcommon.utils.object_hash import Sha256Hash
from bxutils import logging

logger = logging.get_logger(__name__)


def create_txs_service_msg(
    transaction_service: TransactionService,
    tx_service_snap: List[Sha256Hash],
    sync_tx_content: bool = True
) -> List[TxContentShortIds]:
    task_start = time.time()
    txs_content_short_ids: List[TxContentShortIds] = []
    txs_msg_len = 0
    while tx_service_snap:
        transaction_key = transaction_service.get_transaction_key(tx_service_snap.pop())
        short_ids = list(transaction_service.get_short_ids_by_key(transaction_key))
        if sync_tx_content:
            tx_content = transaction_service.get_transaction_by_key(transaction_key)
        else:
            tx_content = bytearray(0)
        # TODO: evaluate short id quota type flag value
        short_id_flags = [transaction_service.get_short_id_transaction_type(short_id) for short_id in short_ids]
        tx_content_short_ids: TxContentShortIds = TxContentShortIds(
            transaction_key.transaction_hash,
            tx_content,
            short_ids,
            short_id_flags
        )

        txs_msg_len += txs_serializer.get_serialized_tx_content_short_ids_bytes_len(tx_content_short_ids)

        txs_content_short_ids.append(tx_content_short_ids)
        if txs_msg_len >= constants.TXS_MSG_SIZE or time.time() - task_start > constants.TXS_SYNC_TASK_DURATION:
            break
    return txs_content_short_ids


# pylint: disable=protected-access
def create_txs_service_msg_from_time(
    transaction_service: TransactionService,
    start_time: float = 0,
    sync_tx_content: bool = True,
    snapshot_cache_keys: Optional[Set[TransactionCacheKeyType]] = None
) -> Tuple[List[TxContentShortIds], float, bool, Set[TransactionCacheKeyType]]:
    task_start = time.time()
    txs_content_short_ids: List[TxContentShortIds] = []
    txs_msg_len = 0
    if snapshot_cache_keys is None:
        snapshot_cache_keys = set()
    done = False
    timestamp = start_time
    expire_short_ids = []
    for short_id, timestamp in transaction_service._tx_assignment_expire_queue.queue.items():
        if timestamp > start_time:
            cache_key = transaction_service._short_id_to_tx_cache_key.get(short_id, None)
            if cache_key is not None:
                transaction_key = transaction_service.get_transaction_key(None, cache_key)
                if cache_key not in snapshot_cache_keys:
                    snapshot_cache_keys.add(transaction_key.transaction_cache_key)
                    short_ids = list(
                        transaction_service._tx_cache_key_to_short_ids[transaction_key.transaction_cache_key]
                    )
                    if sync_tx_content and transaction_service.has_transaction_contents_by_key(transaction_key):
                        tx_content = transaction_service._tx_cache_key_to_contents[
                            transaction_key.transaction_cache_key
                        ]
                    else:
                        tx_content = bytearray(0)
                    short_id_flags = [
                        transaction_service.get_short_id_transaction_type(short_id) for short_id in short_ids
                    ]
                    tx_content_short_ids: TxContentShortIds = TxContentShortIds(
                        transaction_key.transaction_hash,
                        tx_content,
                        short_ids,
                        short_id_flags
                    )
                    txs_msg_len += txs_serializer.get_serialized_tx_content_short_ids_bytes_len(tx_content_short_ids)
                    txs_content_short_ids.append(tx_content_short_ids)
                    if txs_msg_len >= constants.TXS_MSG_SIZE or (
                        time.time() - task_start > constants.TXS_SYNC_TASK_DURATION):
                        break
            else:
                expire_short_ids.append(short_id)
    else:
        done = True
    for short_id in expire_short_ids:
        transaction_service._tx_assignment_expire_queue.remove(short_id)
    return txs_content_short_ids, timestamp, done, snapshot_cache_keys


def create_txs_service_msg_from_buffer(
    transaction_service: TransactionService,
    txs_buffer: memoryview,
    start_offset: int
) -> Tuple[TxServiceSyncTxsMessage, int, int, bool]:
    max_task_complete_time = time.time() + constants.GATEWAY_SYNC_BUILD_MESSAGE_THRESHOLD_S
    current_pos = start_offset
    complete_buffer = False
    tx_count = 0

    if start_offset == 0 and len(txs_buffer) <= constants.GATEWAY_SYNC_MAX_MESSAGE_SIZE_BYTES:
        complete_buffer = True
        tx_count, = struct.unpack_from("<L", txs_buffer)
        start_offset = constants.UL_INT_SIZE_IN_BYTES
        current_pos = len(txs_buffer)
    else:
        if start_offset == 0:
            start_offset = current_pos = constants.UL_INT_SIZE_IN_BYTES

        while not complete_buffer and \
            time.time() < max_task_complete_time and \
            current_pos - start_offset <= constants.GATEWAY_SYNC_MAX_MESSAGE_SIZE_BYTES:

            current_pos += crypto.SHA256_HASH_LEN
            content_len, = struct.unpack_from("<L", txs_buffer, current_pos)

            short_ids_offset = (
                current_pos
                + constants.UL_INT_SIZE_IN_BYTES
                + constants.UL_INT_SIZE_IN_BYTES
                + content_len
            )
            short_ids, = struct.unpack_from("<H", txs_buffer, short_ids_offset)
            current_pos = short_ids_offset + constants.UL_SHORT_SIZE_IN_BYTES + (
                (constants.UL_INT_SIZE_IN_BYTES + constants.TRANSACTION_FLAG_LEN) * short_ids
            )
            tx_count += 1
            if current_pos >= len(txs_buffer):
                complete_buffer = True

    return TxServiceSyncTxsMessage(
        transaction_service.network_num,
        txs_buffer=txs_buffer[start_offset:current_pos],
        tx_count=tx_count,
    ), tx_count, current_pos, complete_buffer
