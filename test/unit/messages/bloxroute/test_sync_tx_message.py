from typing import List

from bxcommon.test_utils.message_factory_test_case import MessageFactoryTestCase
from bxcommon.messages.bloxroute.tx_service_sync_txs_message import TxServiceSyncTxsMessage
from bxcommon.test_utils.mocks.mock_node import MockNode
from bxcommon.utils import crypto
from bxcommon.utils.object_hash import Sha256Hash
from bxcommon.test_utils import helpers
from bxcommon.messages.bloxroute.txs_serializer import TxContentShortIds
from bxcommon.messages.bloxroute import txs_serializer
from bxcommon.services.transaction_service import TransactionService
from bxcommon.messages.bloxroute.bloxroute_message_factory import bloxroute_message_factory
from bxcommon.models.quota_type_model import QuotaType
from bxcommon.services import tx_sync_service_helpers


class SyncTxServiceTest(MessageFactoryTestCase):

    NETWORK_NUM = 12345

    def setUp(self) -> None:
        self.node = MockNode(helpers.get_common_opts(1234))

        self.network_num = 4
        self.transaction_service = TransactionService(self.node, self.network_num)

    def get_message_factory(self):
        return bloxroute_message_factory

    def test_create_message_success_tx_service_sync_txs_msg(self):
        self._test_create_msg_success_tx_service_sync_with_tx_content_count(100)

    def test_create_message_success_tx_service_sync_txs_msg_with_exceeded_buf(self):
        self._test_create_msg_success_tx_service_sync_with_tx_content_count(1000)

    def _test_create_msg_success_tx_service_sync_with_tx_content_count(self, tx_content_count, sync_tx_content=True):
        short_ids = [list(range(1, 6)), list(range(11, 15)), list(range(53, 250)), [31], list(range(41, 48)), [51, 52]]
        transaction_hashes = list(map(crypto.double_sha256, map(bytes, short_ids)))

        for i in range(len(short_ids)):
            transaction_content = bytearray(tx_content_count)
            transaction_content[:32] = transaction_hashes[i]
            self.transaction_service.set_transaction_contents(transaction_hashes[i], transaction_content)
            for short_id in short_ids[i]:
                self.transaction_service.assign_short_id(transaction_hashes[i], short_id)

        # Six blocks received after
        for i in range(len(short_ids)):
            self.transaction_service.track_seen_short_ids(Sha256Hash(helpers.generate_bytearray(32)), short_ids[i])

        tx_service_snap = self.transaction_service.get_snapshot()

        txs_content_short_ids = tx_sync_service_helpers.create_txs_service_msg(
            self.transaction_service, tx_service_snap, sync_tx_content)

        if txs_content_short_ids:
            self._send_tx_msg(txs_content_short_ids, transaction_hashes)

    def _send_tx_msg(self, txs_content_short_ids, transaction_hashes):
        tx_service_sync_txs_msg: TxServiceSyncTxsMessage = \
            self.create_message_successfully(
                TxServiceSyncTxsMessage(
                    self.NETWORK_NUM, txs_content_short_ids
                ),
                TxServiceSyncTxsMessage
            )

        self.assertEqual(self.NETWORK_NUM, tx_service_sync_txs_msg.network_num())
        self.assertEqual(len(txs_content_short_ids), tx_service_sync_txs_msg.tx_count())
        tx_service_txs_content_short_ids = tx_service_sync_txs_msg.txs_content_short_ids()
        tx_contents = [self.transaction_service.get_transaction(short_id).contents
                       for tx_content_short_id in tx_service_txs_content_short_ids for short_id in tx_content_short_id.short_ids]
        for tx_content_short_id in tx_service_txs_content_short_ids:
            self.assertIn(bytearray(tx_content_short_id.tx_hash), transaction_hashes)
            self.assertIn(bytearray(tx_content_short_id.tx_content), tx_contents)
            self.assertEqual(tx_content_short_id.short_ids, list(self.transaction_service.get_short_ids(tx_content_short_id.tx_hash)))
