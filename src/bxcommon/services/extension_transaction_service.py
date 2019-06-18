from bxcommon.services.transaction_service import TransactionService
from bxcommon.utils.object_hash import Sha256Hash
from bxcommon.utils.proxy.default_map_proxy import DefaultMapProxy
from bxcommon.utils.proxy.map_proxy import MapProxy
from bxcommon.utils.object_encoder import ObjectEncoder

import task_pool_executor as tpe  # pyre-ignore for now, figure this out later (stub file or Python wrapper?)


class ExtensionTransactionService(TransactionService):

    def __init__(self, node, network_num):
        super(ExtensionTransactionService, self).__init__(node, network_num)
        self.proxy = tpe.TransactionService()
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

    def _remove_tx_not_seen_in_block(self, transaction_cache_key):
        super(ExtensionTransactionService, self)._remove_tx_not_seen_in_block(transaction_cache_key)
        self.proxy.remove_tx_seen_in_block(transaction_cache_key)

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
