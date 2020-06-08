from bxcommon.messages.bloxroute.ack_message import AckMessage
from bxcommon.messages.bloxroute.bdn_performance_stats_message import BdnPerformanceStatsMessage
from bxcommon.messages.bloxroute.block_confirmation_message import BlockConfirmationMessage
from bxcommon.messages.bloxroute.broadcast_message import BroadcastMessage
from bxcommon.messages.bloxroute.v8.broadcast_message_v8 import BroadcastMessageV8
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
from bxcommon.models.broadcast_message_type import BroadcastMessageType
from bxcommon.test_utils.abstract_bloxroute_version_manager_test import AbstractBloxrouteVersionManagerTest


class BloxrouteVersionManagerV8Test(
    AbstractBloxrouteVersionManagerTest[
        HelloMessage,
        AckMessage,
        PingMessage,
        PongMessage,
        BroadcastMessageV8,
        TxMessage,
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
        return 8

    def old_broadcast_message(self, original_message: BroadcastMessage) -> BroadcastMessageV8:
        return BroadcastMessageV8(
            original_message.block_hash(),
            original_message.network_num(),
            original_message.source_id(),
            original_message.is_encrypted(),
            bytearray(original_message.blob())
        )

    def compare_broadcast_current_to_old(
            self,
            converted_old_message: BroadcastMessageV8,
            original_old_message: BroadcastMessageV8,
    ):
        self.assert_attributes_equal(
            original_old_message,
            converted_old_message,
            [
                "message_hash",
                "network_num",
                "source_id",
                "is_encrypted",
                "blob",
            ],
        )

    def compare_broadcast_old_to_current(
        self,
        converted_current_message: BroadcastMessage,
        original_current_message: BroadcastMessage,
    ):
        self.assertEqual(
            BroadcastMessageType.BLOCK,
            converted_current_message.broadcast_type(),
        )

        self.assert_attributes_equal(
            converted_current_message,
            original_current_message,
            [
                "message_hash",
                "network_num",
                "source_id",
                "is_encrypted",
                "blob",
            ],
        )
