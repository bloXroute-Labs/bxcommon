from typing import List

import time
from unittest import skip

from bxcommon.models.transaction_flag import TransactionFlag
from bxcommon.test_utils.message_factory_test_case import MessageFactoryTestCase

import random
from bxcommon.messages.bloxroute.tx_service_sync_txs_message import TxServiceSyncTxsMessage
from bxcommon.test_utils.mocks.mock_node import MockNode
from bxcommon.utils import crypto
from bxcommon.utils.object_hash import Sha256Hash
from bxcommon.test_utils import helpers
from bxcommon.services.transaction_service import TransactionService
from bxcommon.services import tx_sync_service_helpers


class SyncTxServiceTest(MessageFactoryTestCase):

    NETWORK_NUM = 12345

    def setUp(self) -> None:
        self.node = MockNode(helpers.get_common_opts(1234))

        self.network_num = 4
        self.transaction_service = TransactionService(self.node, self.network_num)

    def _add_transactions(self, tx_count, tx_size, short_id_offset=0):
        short_id = short_id_offset
        for i in range(int(tx_count)):
            tx_hash = Sha256Hash(binary=helpers.generate_bytearray(crypto.SHA256_HASH_LEN))
            tx_content = helpers.generate_bytearray(tx_size)
            transaction_key = self.transaction_service.get_transaction_key(tx_hash)
            self.transaction_service.set_transaction_contents_by_key(transaction_key, tx_content)
            for _ in range(random.randrange(1, 10)):
                short_id += 1
                self.transaction_service.assign_short_id(tx_hash, short_id)
                self.transaction_service.set_short_id_transaction_type(short_id, TransactionFlag.PAID_TX)
                if short_id % 7 < 2:
                    self.transaction_service._short_id_to_tx_cache_key.pop(short_id, None)

    @skip("We don't sync tx service using time")
    def test_create_tx_service_msg(self):
        self._add_transactions(100000, tx_size=50)
        done = False
        msgs = []
        timestamp = 0
        snapshot_cache_keys = None
        total_time = 0
        total_txs = 0
        while not done:
            start_ = time.time()
            txs_content_short_ids, timestamp, done, snapshot_cache_keys = \
                tx_sync_service_helpers.create_txs_service_msg_from_time(
                    self.transaction_service,
                    timestamp,
                    False,
                    snapshot_cache_keys
                )
            duration = time.time() - start_
            total_time += duration
            total_txs += len(txs_content_short_ids)
            msgs.append(txs_content_short_ids)
            # print(f"txs:{len(txs_content_short_ids)}, time: {duration}")
        print(f"total - msgs:{len(msgs)}, time:{total_time}")
        msg_build_time = 0
        for txs_content_short_ids in msgs:
            start_ = time.time()
            msg = TxServiceSyncTxsMessage(self.network_num, txs_content_short_ids)
            duration = time.time() - start_
            msg_build_time += duration
        print(f"total - message creation time: {msg_build_time}")
        self.assertTrue(True)

    @skip("We don't sync tx service using snapshot")
    def test_create_tx_service_msg_snapshot(self):
        self._add_transactions(100000, tx_size=50)
        total_time = 0
        start_ = time.time()
        snapshot = self.transaction_service.get_snapshot(0)
        duration = time.time() - start_
        print(f"snapshot creation: {duration}")
        total_time += duration
        msgs = []

        while snapshot:
            start_ = time.time()
            txs_content_short_ids = tx_sync_service_helpers.create_txs_service_msg(
                self.transaction_service, snapshot, sync_tx_content=False)
            msgs.append(txs_content_short_ids)
            duration = time.time() - start_
            total_time += duration
            # print(len(txs_content_short_ids), duration)
        print(f"total time: {total_time}")

    @skip("We don't sync tx service using snapshot")
    def test_create_tx_service_msg_snapshot_by_time(self):
        self._add_transactions(100000, tx_size=50)
        total_time = 0
        start_ = time.time()
        snapshot = self.transaction_service.get_snapshot(1.0)
        duration = time.time() - start_
        print(f"snapshot creation: {duration}")
        total_time += duration
        msgs = []

        while snapshot:
            start_ = time.time()
            txs_content_short_ids = tx_sync_service_helpers.create_txs_service_msg(
                self.transaction_service, snapshot, sync_tx_content=False)
            msgs.append(txs_content_short_ids)
            duration = time.time() - start_
            total_time += duration
            # print(len(txs_content_short_ids), duration)
        print(f"total time: {total_time}")
