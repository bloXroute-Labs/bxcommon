from bxcommon import constants
from bxcommon.messages.bloxroute.ack_message import AckMessage
from bxcommon.messages.bloxroute.bdn_performance_stats_message import BdnPerformanceStatsMessage
from bxcommon.messages.bloxroute.block_confirmation_message import BlockConfirmationMessage
from bxcommon.messages.bloxroute.broadcast_message import BroadcastMessage
from bxcommon.messages.bloxroute.get_txs_message import GetTxsMessage
from bxcommon.messages.bloxroute.hello_message import HelloMessage
from bxcommon.messages.bloxroute.key_message import KeyMessage
from bxcommon.messages.bloxroute.notification_message import NotificationMessage
from bxcommon.messages.bloxroute.ping_message import PingMessage
from bxcommon.messages.bloxroute.pong_message import PongMessage
from bxcommon.messages.bloxroute.transaction_cleanup_message import TransactionCleanupMessage
from bxcommon.messages.bloxroute.tx_message import TxMessage
from bxcommon.messages.bloxroute.tx_service_sync_blocks_short_ids_message import TxServiceSyncBlocksShortIdsMessage
from bxcommon.messages.bloxroute.tx_service_sync_complete_message import TxServiceSyncCompleteMessage
from bxcommon.messages.bloxroute.tx_service_sync_req_message import TxServiceSyncReqMessage
from bxcommon.messages.bloxroute.tx_service_sync_txs_message import TxServiceSyncTxsMessage
from bxcommon.messages.bloxroute.txs_message import TxsMessage
from bxcommon.messages.bloxroute.v13.pong_message_v13 import PongMessageV13
from bxcommon.messages.bloxroute.v7.tx_message_v7 import TxMessageV7
from bxcommon.test_utils.abstract_bloxroute_version_manager_test import AbstractBloxrouteVersionManagerTest


class BloxrouteVersionManagerV7Test(
    AbstractBloxrouteVersionManagerTest[
        HelloMessage,
        AckMessage,
        PingMessage,
        PongMessageV13,
        BroadcastMessage,
        TxMessageV7,
        GetTxsMessage,
        TxsMessage,
        KeyMessage,
        TxServiceSyncReqMessage,
        TxServiceSyncBlocksShortIdsMessage,
        TxServiceSyncTxsMessage,
        TxServiceSyncCompleteMessage,
        BlockConfirmationMessage,
        TransactionCleanupMessage,
        NotificationMessage,
        BdnPerformanceStatsMessage,
    ]
):
    def version_to_test(self) -> int:
        return 7

    def old_tx_message(self, original_message: TxMessage) -> TxMessageV7:
        return TxMessageV7(
            original_message.message_hash(),
            original_message.network_num(),
            original_message.source_id(),
            original_message.short_id(),
            original_message.tx_val(),
            original_message.transaction_flag().get_quota_type(),
        )

    def compare_tx_current_to_old(
        self,
        converted_old_message: TxMessageV7,
        original_old_message: TxMessageV7,
    ):
        self.assert_attributes_equal(
            original_old_message,
            converted_old_message,
            [
                "message_hash",
                "tx_val",
                "source_id",
                "network_num",
                "quota_type",
            ],
        )

    def compare_tx_old_to_current(
        self,
        converted_current_message: TxMessage,
        original_current_message: TxMessage,
    ):
        self.assertEqual(
            constants.NULL_TX_TIMESTAMP, converted_current_message.timestamp()
        )
        self.assert_attributes_equal(
            converted_current_message,
            original_current_message,
            [
                "message_hash",
                "tx_val",
                "source_id",
                "network_num",
                "quota_type",
            ],
        )

    def old_pong_message(self, original_message: PongMessage) -> PongMessageV13:
        return PongMessageV13(original_message.nonce())

    def test_tx_message(self):
        pass

    def test_txtxs_message(self):
        pass

    def test_bdn_performance_stats_message(self):
        pass

    def test_broadcast_message(self):
        pass
