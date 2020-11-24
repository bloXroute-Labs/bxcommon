import struct
import time
from datetime import datetime
from typing import Any, List, Union, Optional

import task_pool_executor as tpe

from bxcommon import constants
from bxcommon.messages.bloxroute import transactions_info_serializer
from bxcommon.messages.bloxroute.tx_service_sync_txs_message import TxServiceSyncTxsMessage
from bxcommon.models.transaction_flag import TransactionFlag
from bxcommon.models.transaction_info import TransactionSearchResult, TransactionInfo
from bxcommon.models.transaction_key import TransactionKey, TransactionCacheKeyType
from bxcommon.services.transaction_service import TransactionService, TxSyncMsgProcessingItem
from bxcommon.services.transaction_service import TxRemovalReason
from bxcommon.utils import memory_utils, crypto
from bxcommon.utils.deprecated import deprecated
from bxcommon.utils.memory_utils import ObjectSize, SizeType
from bxcommon.utils.object_encoder import ObjectEncoder
from bxcommon.utils.object_hash import Sha256Hash
from bxcommon.utils.proxy import task_pool_proxy
from bxcommon.utils.proxy.default_map_proxy import DefaultMapProxy
from bxcommon.utils.proxy.map_proxy import MapProxy
from bxcommon.utils.stats import hooks
from bxcommon.utils.stats.transaction_stat_event_type import TransactionStatEventType
from bxcommon.utils.stats.transaction_statistics_service import tx_stats
from bxutils import logging
from bxutils.logging import log_config
from bxutils.logging.log_record_type import LogRecordType

logger = logging.get_logger(__name__)
logger_memory_cleanup = logging.get_logger(LogRecordType.BlockCleanup, __name__)

UNKNOWN_TRANSACTION_HASH: Sha256Hash = Sha256Hash(bytearray(b"\xff" * crypto.SHA256_HASH_LEN))


class ExtensionTransactionService(TransactionService):

    def __init__(self, node, network_num) -> None:
        super(ExtensionTransactionService, self).__init__(node, network_num)
        # Log levels need to be set again to include the loggers created in this conditionally imported class
        log_config.lazy_set_log_level(node.opts.log_level_overrides)

        self.proxy = tpe.TransactionService(
            task_pool_proxy.get_pool_size(),
            self.node.opts.blockchain_networks[network_num].protocol.lower(),
            node.opts.tx_mem_pool_bucket_size,
            self._get_final_tx_confirmations_count()
        )
        raw_encoder = ObjectEncoder.raw_encoder()
        self._tx_cache_key_to_short_ids = DefaultMapProxy(
            self.proxy.tx_hash_to_short_ids(), raw_encoder, raw_encoder
        )
        self._short_id_to_tx_cache_key = MapProxy(
            self.proxy.short_id_to_tx_hash(), raw_encoder, raw_encoder
        )
        # pyre-fixme[6]: Incompatible parameter type
        content_encoder = ObjectEncoder(memoryview, tpe.InputBytes)
        self._tx_cache_key_to_contents = MapProxy(
            # pyre-fixme[6]: Incompatible parameter type
            self.proxy.tx_hash_to_contents(), raw_encoder, content_encoder
        )
        self._tx_not_seen_in_blocks = self.proxy.tx_not_seen_in_blocks()

        self._tx_hash_to_time_removed = MapProxy(
            self.proxy.tx_hash_to_time_removed(), raw_encoder, raw_encoder
        )
        self._short_id_to_time_removed = MapProxy(
            self.proxy.short_id_to_time_removed(), raw_encoder, raw_encoder
        )

    def track_seen_short_ids(self, block_hash, short_ids: List[int]) -> None:
        start_datetime = datetime.now()
        super(ExtensionTransactionService, self).track_seen_short_ids(block_hash, short_ids)
        wrapped_block_hash = tpe.Sha256(tpe.InputBytes(self._wrap_sha256(block_hash).binary))
        proxy_start_datetime = datetime.now()
        # TODO when refactoring add `block_hash` to proxy.track_seen_short_ids as
        # first parameter and change ds type in cpp
        result = self.proxy.track_seen_short_ids(wrapped_block_hash, tpe.UIntList(short_ids))
        removed_contents_size, dup_sids = result
        self.update_removed_transactions(removed_contents_size, dup_sids)
        logger_memory_cleanup.statistics(
            {
                "type": "MemoryCleanup",
                "event": "ExtensionTransactionServiceTrackSeenSummary",
                "seen_short_ids_count": len(short_ids),
                "total_content_size_removed": removed_contents_size,
                "total_duplicate_short_ids": len(dup_sids),
                "proxy_call_datetime": proxy_start_datetime,
                "data": self.get_cache_state_json(),
                "start_datetime": start_datetime,
                "block_hash": repr(block_hash)
            }
        )

    def set_final_tx_confirmations_count(self, val: int):
        super(ExtensionTransactionService, self).set_final_tx_confirmations_count(val)
        self.proxy.set_final_tx_confirmations_count(val)

    def on_block_cleaned_up(self, block_hash: Sha256Hash) -> None:
        super(ExtensionTransactionService, self).on_block_cleaned_up(block_hash)
        wrapped_block_hash = tpe.Sha256(tpe.InputBytes(block_hash.binary))
        self.proxy.on_block_cleaned_up(wrapped_block_hash)

    def get_tx_service_sync_buffer(self, sync_tx_content: bool) -> memoryview:
        byte_array_obj = self.proxy.get_tx_sync_buffer(
            self._total_tx_contents_size, sync_tx_content
        )
        return memoryview(byte_array_obj)

    def update_removed_transactions(self, removed_content_size: int, short_ids: List[int]) -> None:
        self._total_tx_contents_size -= removed_content_size
        for short_id in short_ids:
            tx_stats.add_tx_by_hash_event(
                UNKNOWN_TRANSACTION_HASH, TransactionStatEventType.TX_REMOVED_FROM_MEMORY,
                self.network_num, short_id, reason=TxRemovalReason.EXTENSION_BLOCK_CLEANUP.value
            )
            self._tx_assignment_expire_queue.remove(short_id)
            if self.node.opts.dump_removed_short_ids:
                self._removed_short_ids.add(short_id)

    @deprecated
    def assign_short_id(
        self,
        transaction_hash: Sha256Hash,
        short_id: int,
        transaction_cache_key: Optional[TransactionCacheKeyType] = None
    ) -> None:
        return self.assign_short_id_by_key(
            self.get_transaction_key(transaction_hash, transaction_cache_key),
            short_id,
        )

    def assign_short_id_by_key(
        self,
        transaction_key: TransactionKey,
        short_id: int,
    ) -> None:
        """
        Adds short id mapping for transaction and schedules an alarm to cleanup entry on expiration.
        :param transaction_key: transaction key object
        :param short_id: short id to be mapped to transaction
        """
        logger.trace("Assigning sid {} to transaction {}", short_id, transaction_key.transaction_hash)

        # pyre-fixme[6]: Expected `tpe.Sha256` got `TransactionCacheKeyType`.
        has_contents = self.proxy.assign_short_id(transaction_key.transaction_cache_key, short_id)
        self.assign_short_id_base_by_key(transaction_key, short_id, has_contents, False)

    @deprecated
    def set_transaction_contents(
        self, transaction_hash: Sha256Hash, transaction_contents: Union[bytearray, memoryview],
        transaction_cache_key: Optional[TransactionCacheKeyType] = None
    ):
        return self.set_transaction_contents_by_key(
            self.get_transaction_key(transaction_hash, transaction_cache_key),
            transaction_contents
        )

    def set_transaction_contents_by_key(
        self, transaction_key: TransactionKey, transaction_contents: Union[bytearray, memoryview]
    ):
        """
        Adds transaction contents to transaction service cache with lookup key by transaction hash

        :param transaction_key: transaction key object
        :param transaction_contents: transaction contents bytes
        """
        has_short_id, previous_size = self.proxy.set_transaction_contents(
            # pyre-fixme[6]: Expected `tpe.Sha256` got `TransactionCacheKeyType`.
            transaction_key.transaction_cache_key,
            tpe.InputBytes(transaction_contents))

        self.set_transaction_contents_base_by_key(
            transaction_key,
            has_short_id,
            previous_size,
            False,
            transaction_contents,
            len(transaction_contents)
        )

    def get_transactions(
        self,
        serialized_short_ids: Optional[bytearray] = None
    ) -> TransactionSearchResult:
        """
        Fetches all transaction info for a set of short ids.
        Short ids without a transaction entry will be omitted.
        Function allows to pass a single short id or serialized list of short ids
        :param serialized_short_ids: instance of get transactions message
        :return: list of found and missing short ids
        """

        assert serialized_short_ids is not None
        input_bytes = tpe.InputBytes(serialized_short_ids)

        result_bytes = self.proxy.get_transactions_by_short_ids(input_bytes)
        assert result_bytes is not None
        result_memory_view = memoryview(result_bytes)

        found_txs_size, = struct.unpack_from("<L", result_memory_view, 0)

        txs_bytes = result_memory_view[constants.UL_INT_SIZE_IN_BYTES:constants.UL_INT_SIZE_IN_BYTES + found_txs_size]
        found_txs_info = transactions_info_serializer \
            .deserialize_transactions_info(txs_bytes)

        missing_txs_info = []
        offset = constants.UL_INT_SIZE_IN_BYTES + found_txs_size

        missing_txs_count, = struct.unpack_from("<L", result_memory_view, offset)
        offset += constants.UL_INT_SIZE_IN_BYTES

        for _ in range(missing_txs_count):
            tx_sid, = struct.unpack_from("<L", result_memory_view, offset)
            offset += constants.UL_INT_SIZE_IN_BYTES

            has_hash, = struct.unpack_from("<B", result_memory_view, offset)
            offset += constants.UL_TINY_SIZE_IN_BYTES

            if has_hash:
                tx_hash = Sha256Hash(result_memory_view[offset:offset + crypto.SHA256_HASH_LEN])
                offset += crypto.SHA256_HASH_LEN
            else:
                tx_hash = None

            missing_txs_info.append(TransactionInfo(tx_hash, None, tx_sid))

        return TransactionSearchResult(found_txs_info, missing_txs_info)

    def process_tx_sync_message(self, msg: TxServiceSyncTxsMessage) -> List[TxSyncMsgProcessingItem]:
        input_bytes = tpe.InputBytes(msg.rawbytes())
        result_bytes = self.proxy.process_tx_sync_message(input_bytes)

        assert result_bytes is not None
        result_memory_view = memoryview(result_bytes)

        result_items = []
        offset = 0

        txs_count, = struct.unpack_from("<L", result_memory_view, offset)
        offset += constants.UL_INT_SIZE_IN_BYTES

        for _ in range(txs_count):
            transaction_hash = Sha256Hash(result_memory_view[offset:offset + crypto.SHA256_HASH_LEN])
            transaction_key = self.get_transaction_key(transaction_hash)
            offset += crypto.SHA256_HASH_LEN

            content_len, = struct.unpack_from("<L", result_memory_view, offset)
            offset += constants.UL_INT_SIZE_IN_BYTES

            short_id_count, = struct.unpack_from("<L", result_memory_view, offset)
            offset += constants.UL_INT_SIZE_IN_BYTES

            if content_len > 0:
                self.set_transaction_contents_base_by_key(
                    transaction_key,
                    short_id_count > 0,
                    0,
                    False,
                    None,
                    content_len
                )

            short_ids = []

            for _ in range(short_id_count):
                short_id, = struct.unpack_from("<L", result_memory_view, offset)
                offset += constants.UL_INT_SIZE_IN_BYTES

                self.assign_short_id_base_by_key(
                    transaction_key,
                    short_id,
                    content_len > 0,
                    False
                )

                short_ids.append(short_id)

            transaction_flags = []

            for _ in range(short_id_count):
                transaction_flag, = struct.unpack_from("<H", result_memory_view, offset)
                offset += constants.TRANSACTION_FLAG_LEN
                transaction_flags.append(TransactionFlag(transaction_flag))

            result_items.append(TxSyncMsgProcessingItem(transaction_hash, content_len, short_ids, transaction_flags))

        return result_items

    def log_tx_service_mem_stats(self, include_data_structure_memory: bool = False) -> None:
        super(ExtensionTransactionService, self).log_tx_service_mem_stats(include_data_structure_memory)

        if include_data_structure_memory:
            hooks.add_obj_mem_stats(
                self.__class__.__name__,
                self.network_num,
                self._tx_not_seen_in_blocks,
                "tx_not_seen_in_blocks",
                self.get_collection_mem_stats(SizeType.OBJECT, self._tx_not_seen_in_blocks),
                object_item_count=len(self._tx_not_seen_in_blocks),
                object_type=memory_utils.ObjectType.BASE,
                size_type=SizeType.OBJECT
            )

    def get_collection_mem_stats(self, size_type: SizeType, collection_obj: Any, estimated_size: int = 0) -> ObjectSize:
        if self.get_object_type(collection_obj) == memory_utils.ObjectType.DEFAULT_MAP_PROXY:
            collection_size = collection_obj.map_obj.get_bytes_length()
            if collection_obj is self._tx_cache_key_to_short_ids:
                collection_size += (
                    len(self._short_id_to_tx_cache_key) * constants.UL_INT_SIZE_IN_BYTES)
            return memory_utils.ObjectSize(size=collection_size, flat_size=0, is_actual_size=True)
        else:
            return super(ExtensionTransactionService, self).get_collection_mem_stats(
                size_type, collection_obj, estimated_size
            )

    def get_object_type(self, collection_obj: Any):
        super(ExtensionTransactionService, self).get_object_type(collection_obj)
        if isinstance(collection_obj, DefaultMapProxy):
            return memory_utils.ObjectType.DEFAULT_MAP_PROXY
        elif isinstance(collection_obj, MapProxy):
            return memory_utils.ObjectType.MAP_PROXY
        else:
            return memory_utils.ObjectType.BASE

    def get_oldest_removed_tx_hash(self, tx_hashes: List[Sha256Hash]) -> float:
        oldest_removed_tx_hash = 0
        for tx_hash in tx_hashes:
            if tx_hash in self._tx_hash_to_time_removed and \
                    oldest_removed_tx_hash < self._tx_hash_to_time_removed[tx_hash]:
                oldest_removed_tx_hash = self._tx_hash_to_time_removed[tx_hash]
        return oldest_removed_tx_hash

    def get_oldest_removed_short_id(self, short_ids: List[int]) -> float:
        oldest_removed_short_id = 0
        for short_id in short_ids:
            if short_id in self._short_id_to_time_removed and \
                    oldest_removed_short_id < self._short_id_to_time_removed[short_id]:
                oldest_removed_short_id = self._short_id_to_time_removed[short_id]
        return oldest_removed_short_id

    def _tx_hash_to_cache_key(self, transaction_hash) -> tpe.Sha256:  # pyre-ignore
        if isinstance(transaction_hash, Sha256Hash):
            return tpe.Sha256(tpe.InputBytes(transaction_hash.binary))

        if isinstance(transaction_hash, (bytes, bytearray, memoryview)):
            return tpe.Sha256(tpe.InputBytes(transaction_hash))

        if isinstance(transaction_hash, tpe.Sha256):
            return transaction_hash

        raise ValueError("Attempted to find cache entry with incorrect key type")

        # return transaction_hash

    def _tx_cache_key_to_hash(self, transaction_cache_key) -> Sha256Hash:
        if isinstance(transaction_cache_key, Sha256Hash):
            return transaction_cache_key

        if isinstance(transaction_cache_key, (bytes, bytearray, memoryview)):
            return Sha256Hash(transaction_cache_key)

        return Sha256Hash(bytearray(transaction_cache_key.binary()))

    def _track_seen_transaction(self, transaction_cache_key):
        super(ExtensionTransactionService, self)._track_seen_transaction(transaction_cache_key)
        self.proxy.track_seen_transaction(transaction_cache_key)

    def remove_transaction_by_short_id(self, short_id: int, remove_related_short_ids: bool = False,
                                       force: bool = False,
                                       removal_reason: TxRemovalReason = TxRemovalReason.UNKNOWN):
        # overriding this in order to handle removes triggered by either the mem limit or expiration queue
        # if the remove_related_short_ids is True than we assume the call originated by the track seen call
        # else we assume it was triggered by the cleanup.
        # this is only a temporary fix and the whole class hierarchy requires some refactoring!
        if remove_related_short_ids:
            self._tx_assignment_expire_queue.remove(short_id)
            tx_stats.add_tx_by_hash_event(
                UNKNOWN_TRANSACTION_HASH, TransactionStatEventType.TX_REMOVED_FROM_MEMORY,
                self.network_num, short_id, reason=removal_reason.value
            )
            if self.node.opts.dump_removed_short_ids:
                self._removed_short_ids.add(short_id)
        else:
            super(
                ExtensionTransactionService, self
            ).remove_transaction_by_short_id(
                short_id,
                force=force,
                removal_reason=removal_reason
            )

    def clear(self):
        self.proxy.clear()

        self._short_id_to_tx_flag.clear()
        self.tx_hashes_without_content.clear()
        self.tx_hashes_without_short_id.clear()
        self._tx_assignment_expire_queue.clear()
        self._total_tx_contents_size = 0

    def _cleanup_removed_transactions_history(self):
        logger.trace(
            "Starting to cleanup transaction cache history for network "
            "number: {}.",
            self.network_num
        )
        current_time = time.time()
        tx_hash_history_len_before = len(self._tx_hash_to_time_removed)
        self._tx_hash_to_time_removed.map_obj.cleanup_removed_hashes_history(
            current_time, self._removed_txs_expiration_time_s, constants.REMOVED_TRANSACTIONS_HISTORY_LENGTH_LIMIT
        )
        tx_hash_history_len_after = len(self._tx_hash_to_time_removed)

        short_id_history_len_before = len(self._short_id_to_time_removed)
        self._short_id_to_time_removed.map_obj.cleanup_removed_short_ids_history(
            current_time, self._removed_txs_expiration_time_s, constants.REMOVED_TRANSACTIONS_HISTORY_LENGTH_LIMIT
        )
        short_id_history_len_after = len(self._short_id_to_time_removed)
        logger.trace(
            "Finished cleanup transaction cache history. "
            "tx_hash size before: {}, size after: {}."
            "short_id size before: {}, size after: {}.",
            tx_hash_history_len_before,
            tx_hash_history_len_after,
            short_id_history_len_before,
            short_id_history_len_after
        )

        return constants.REMOVED_TRANSACTIONS_HISTORY_CLEANUP_INTERVAL_S
