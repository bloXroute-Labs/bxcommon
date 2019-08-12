from datetime import datetime

import task_pool_executor as tpe  # pyre-ignore for now, figure this out later (stub file or Python wrapper?)

from bxcommon.services.transaction_service import TransactionService
from bxcommon.utils import logger
from bxcommon.utils.object_encoder import ObjectEncoder
from bxcommon.utils.object_hash import Sha256Hash
from bxcommon.utils.proxy import task_pool_proxy
from bxcommon.utils.proxy.default_map_proxy import DefaultMapProxy
from bxcommon.utils.proxy.map_proxy import MapProxy


class ExtensionTransactionService(TransactionService):

    def __init__(self, node, network_num):
        super(ExtensionTransactionService, self).__init__(node, network_num)
        self.proxy = tpe.TransactionService(
            task_pool_proxy.get_pool_size(),
            node.opts.tx_mem_pool_bucket_size,
            self._get_final_tx_confirmations_count()
        )
        raw_encoder = ObjectEncoder.raw_encoder()
        self._tx_hash_to_short_ids = DefaultMapProxy(
            self.proxy.tx_hash_to_short_ids(), raw_encoder, raw_encoder
        )
        self._short_id_to_tx_hash = MapProxy(
            self.proxy.short_id_to_tx_hash(), raw_encoder, raw_encoder
        )
        content_encoder = ObjectEncoder(
            lambda buf_view: memoryview(buf_view),
            lambda buf: tpe.InputBytes(buf)
        )
        self._tx_hash_to_contents = MapProxy(
            self.proxy.tx_hash_to_contents(), raw_encoder, content_encoder
        )

    def track_seen_short_ids(self, short_ids):
        start_datetime = datetime.now()
        super(ExtensionTransactionService, self).track_seen_short_ids(short_ids)
        proxy_start_datetime = datetime.now()
        result = self.proxy.track_seen_short_ids(tpe.UIntList(short_ids))
        removed_contents_size, dup_sids = result
        self._total_tx_contents_size -= removed_contents_size
        for dup_sid in dup_sids:
            self._tx_assignment_expire_queue.remove(dup_sid)
        logger.info(
            f"finished tracking {len(short_ids)} seen short ids, "
            f"removed total {removed_contents_size} bytes, "
            f"cleaned up {len(dup_sids)}, started at {start_datetime}, "
            f"proxy called at {proxy_start_datetime}."
        )
        logger.info(
            f"Transaction cache state after tracking seen short ids in extension: {self._get_cache_state_str()}")

    def set_final_tx_confirmations_count(self, val: int):
        super(ExtensionTransactionService, self).set_final_tx_confirmations_count(val)
        self.proxy.set_final_tx_confirmations_count(val)

    def _tx_hash_to_cache_key(self, transaction_hash):

        if isinstance(transaction_hash, Sha256Hash):
            return tpe.Sha256(tpe.InputBytes(transaction_hash.binary))

        if isinstance(transaction_hash, (bytes, bytearray, memoryview)):
            return tpe.Sha256(tpe.InputBytes(transaction_hash))

        return transaction_hash

    def _tx_cache_key_to_hash(self, transaction_cache_key):
        if isinstance(transaction_cache_key, Sha256Hash):
            return transaction_cache_key

        if isinstance(transaction_cache_key, (bytes, bytearray, memoryview)):
            return Sha256Hash(transaction_cache_key)

        return Sha256Hash(bytearray(transaction_cache_key.binary()))

    def _track_seen_transaction(self, transaction_cache_key):
        super(ExtensionTransactionService, self)._track_seen_transaction(transaction_cache_key)
        self.proxy.track_seen_transaction(transaction_cache_key)

    def _remove_transaction_by_short_id(self, short_id, remove_related_short_ids=False):
        # overriding this in order to handle removes triggered by either the mem limit or expiration queue
        # if the remove_related_short_ids is True than we assume the call originated by the track seen call
        # else we assume it was triggered by the cleanup.
        # this is only a temporary fix and the whole class hierarchy requires some refactoring!
        if remove_related_short_ids:
            self._tx_assignment_expire_queue.remove(short_id)
            if self.node.opts.dump_removed_short_ids:
                self._removed_short_ids.add(short_id)
        else:
            super(ExtensionTransactionService, self)._remove_transaction_by_short_id(short_id)
