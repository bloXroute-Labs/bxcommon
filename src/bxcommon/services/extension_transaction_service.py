import time
from datetime import datetime
from typing import Any, List, Union, Optional

import task_pool_executor as tpe

from bxcommon import constants
from bxcommon.services.transaction_service import TransactionService, TransactionCacheKeyType, \
    TransactionFromBdnGatewayProcessingResult
from bxcommon.services.transaction_service import TxRemovalReason
from bxcommon.utils import memory_utils
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


class ExtensionTransactionService(TransactionService):

    def __init__(self, node, network_num):
        super(ExtensionTransactionService, self).__init__(node, network_num)

        # Log levels need to be set again to include the loggers created in this conditionally imported class
        log_config.lazy_set_log_level(node.opts.log_level_overrides)

        self.proxy = tpe.TransactionService(
            task_pool_proxy.get_pool_size(),
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
        content_encoder = ObjectEncoder(memoryview, tpe.InputBytes)
        self._tx_cache_key_to_contents = MapProxy(
            self.proxy.tx_hash_to_contents(), raw_encoder, content_encoder
        )
        self._tx_not_seen_in_blocks = self.proxy.tx_not_seen_in_blocks()

        self._tx_hash_to_time_removed = MapProxy(
            self.proxy.tx_hash_to_time_removed(), raw_encoder, raw_encoder
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
        byte_array_obj = self.proxy.get_tx_sync_buffer(self._total_tx_contents_size,
                                                       sync_tx_content)
        return memoryview(byte_array_obj)

    def update_removed_transactions(self, removed_content_size: int, short_ids: List[int]) -> None:
        self._total_tx_contents_size -= removed_content_size
        for short_id in short_ids:
            tx_stats.add_tx_by_hash_event(
                constants.UNKNOWN_TRANSACTION_HASH, TransactionStatEventType.TX_REMOVED_FROM_MEMORY,
                self.network_num, short_id, reason=TxRemovalReason.EXTENSION_BLOCK_CLEANUP.value
            )
            self._tx_assignment_expire_queue.remove(short_id)
            if self.node.opts.dump_removed_short_ids:
                self._removed_short_ids.add(short_id)

    def assign_short_id(self, transaction_hash: Sha256Hash, short_id: int):
        """
        Adds short id mapping for transaction and schedules an alarm to cleanup entry on expiration.
        :param transaction_hash: transaction long hash
        :param short_id: short id to be mapped to transaction
        """
        logger.trace("Assigning sid {} to transaction {}", short_id, transaction_hash)
        tx_cache_key = self._tx_hash_to_cache_key(transaction_hash)
        has_contents = self.proxy.assign_short_id(tx_cache_key, short_id)
        self.assign_short_id_base(transaction_hash, tx_cache_key, short_id, has_contents, False)

    def set_transaction_contents(
        self, transaction_hash: Sha256Hash, transaction_contents: Union[bytearray, memoryview],
        transaction_cache_key: Optional[TransactionCacheKeyType] = None
    ):
        """
        Adds transaction contents to transaction service cache with lookup key by transaction hash

        :param transaction_hash: transaction hash
        :param transaction_contents: transaction contents bytes
        :param transaction_cache_key: transaction cache key optional
        """
        if not transaction_cache_key:
            transaction_cache_key = self._tx_hash_to_cache_key(transaction_hash)

        assert isinstance(transaction_cache_key, tpe.Sha256)
        has_short_id, previous_size = self.proxy.set_transaction_contents(
            transaction_cache_key,
            tpe.InputBytes(transaction_contents))

        self.set_transaction_contents_base(
            transaction_hash,
            transaction_cache_key,
            transaction_contents,
            has_short_id,
            previous_size,
            False
        )

    def process_gateway_transaction_from_bdn(
        self,
        transaction_hash: Sha256Hash,
        short_id: int,
        transaction_contents: Union[bytearray, memoryview],
        is_compact: bool
    ) -> TransactionFromBdnGatewayProcessingResult:

        transaction_cache_key = self._tx_hash_to_cache_key(transaction_hash)

        ext_result = self.proxy.process_gateway_transaction_from_bdn(
            transaction_cache_key,
            tpe.InputBytes(transaction_contents),
            short_id,
            is_compact
        )

        result = TransactionFromBdnGatewayProcessingResult(
            ext_result.get_ignore_seen(),
            ext_result.get_existing_short_id(),
            ext_result.get_assigned_short_id(),
            ext_result.get_existing_contents(),
            ext_result.get_set_contents()
        )

        if result.set_content:
            has_short_id, previous_size = ext_result.get_set_contents_result()
            self.set_transaction_contents_base(
                transaction_hash,
                transaction_cache_key,
                transaction_contents,
                has_short_id,
                previous_size,
                False
            )

        if result.assigned_short_id:
            has_contents = result.existing_contents or result.set_content
            self.assign_short_id_base(
                transaction_hash,
                transaction_cache_key,
                short_id,
                has_contents,
                False
            )

        return result

    def log_tx_service_mem_stats(self):
        super(ExtensionTransactionService, self).log_tx_service_mem_stats()
        if self.node.opts.stats_calculate_actual_size:
            size_type = memory_utils.SizeType.OBJECT
        else:
            size_type = memory_utils.SizeType.ESTIMATE
        hooks.add_obj_mem_stats(
            self.__class__.__name__,
            self.network_num,
            self._tx_not_seen_in_blocks,
            "tx_not_seen_in_blocks",
            self.get_collection_mem_stats(
                self._tx_not_seen_in_blocks),
            object_item_count=len(self._tx_not_seen_in_blocks),
            object_type=memory_utils.ObjectType.BASE,
            size_type=size_type
        )

    def get_collection_mem_stats(self, collection_obj: Any,
                                 estimated_size: int = 0) -> memory_utils.ObjectSize:
        if self.get_object_type(collection_obj) == memory_utils.ObjectType.DEFAULT_MAP_PROXY:
            collection_size = collection_obj.map_obj.get_bytes_length()
            if collection_obj is self._tx_cache_key_to_short_ids:
                collection_size += (
                    len(self._short_id_to_tx_cache_key) * constants.UL_INT_SIZE_IN_BYTES)
            return memory_utils.ObjectSize(size=collection_size, flat_size=0, is_actual_size=True)
        else:
            return super(ExtensionTransactionService, self).get_collection_mem_stats(collection_obj,
                                                                                     estimated_size)

    def get_object_type(self, collection_obj: Any):
        super(ExtensionTransactionService, self).get_object_type(collection_obj)
        if isinstance(collection_obj, DefaultMapProxy):
            return memory_utils.ObjectType.DEFAULT_MAP_PROXY
        elif isinstance(collection_obj, MapProxy):
            return memory_utils.ObjectType.MAP_PROXY
        else:
            return memory_utils.ObjectType.BASE

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
                constants.UNKNOWN_TRANSACTION_HASH, TransactionStatEventType.TX_REMOVED_FROM_MEMORY,
                self.network_num, short_id, reason=removal_reason.value
            )
            if self.node.opts.dump_removed_short_ids:
                self._removed_short_ids.add(short_id)
        else:
            super(ExtensionTransactionService, self).remove_transaction_by_short_id(short_id,
                                                                                    force=force,
                                                                                    removal_reason=removal_reason)

    def _clear(self):
        super(ExtensionTransactionService, self)._clear()
        self.proxy.clear_short_ids_seen_in_block()

    def _cleanup_removed_transactions_history(self):
        logger.trace(
            "Starting to cleanup transaction cache history for network "
            "number: {}.",
            self.network_num
        )
        history_len_before = len(self._tx_hash_to_time_removed)
        self._tx_hash_to_time_removed.map_obj.cleanup_removed_hashes_history(
            time.time(), self._removed_txs_expiration_time_s, constants.REMOVED_TRANSACTIONS_HISTORY_LENGTH_LIMIT
        )
        history_len_after = len(self._tx_hash_to_time_removed)
        logger.trace(
            "Finished cleanup transaction cache history. Size before: {}. "
            "Size after: {}.",
            history_len_before,
            history_len_after
        )

        return constants.REMOVED_TRANSACTIONS_HISTORY_CLEANUP_INTERVAL_S
