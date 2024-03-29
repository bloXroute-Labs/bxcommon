import time

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
from bxcommon.messages.bloxroute.v16.bdn_performance_stats_message_v16 import \
    BdnPerformanceStatsMessageV16
from bxcommon.messages.bloxroute.v17.tx_message_v17 import TxMessageV17
from bxcommon.test_utils.abstract_bloxroute_version_manager_test import AbstractBloxrouteVersionManagerTest


class BloxrouteVersionManagerV16Test(
    AbstractBloxrouteVersionManagerTest[
        HelloMessage,
        AckMessage,
        PingMessage,
        PongMessage,
        BroadcastMessage,
        TxMessageV17,
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
        BdnPerformanceStatsMessageV16
    ]
):

    def version_to_test(self) -> int:
        return 16

    def old_tx_message(self, original_message: TxMessage) -> TxMessageV17:
        return TxMessageV17(
            original_message.message_hash(),
            original_message.network_num(),
            original_message.source_id(),
            original_message.short_id(),
            original_message.tx_val(),
            original_message.transaction_flag(),
            int(original_message.timestamp()),
        )

    def compare_tx_old_to_current(
        self,
        converted_current_message: TxMessage,
        original_current_message: TxMessage,
    ):
        self.assertEqual(
            int(original_current_message.timestamp()), converted_current_message.timestamp()
        )
        self.assert_attributes_equal(
            converted_current_message,
            original_current_message,
            [
                "message_hash",
                "tx_val",
                "source_id",
                "network_num",
                "transaction_flag",
            ],
        )

    def old_bdn_performance_stats_message(
        self, original_message: BdnPerformanceStatsMessage
    ) -> BdnPerformanceStatsMessageV16:
        _, single_node_stats = next(iter(original_message.node_stats().items()))
        return BdnPerformanceStatsMessageV16(
            original_message.interval_start_time(),
            original_message.interval_end_time(),
            single_node_stats.new_blocks_received_from_blockchain_node,
            single_node_stats.new_blocks_received_from_bdn,
            single_node_stats.new_tx_received_from_blockchain_node,
            single_node_stats.new_tx_received_from_bdn,
            original_message.memory_utilization(),
            single_node_stats.new_blocks_seen,
            single_node_stats.new_block_messages_from_blockchain_node,
            single_node_stats.new_block_announcements_from_blockchain_node
        )

    def compare_bdn_performance_stats_old_to_current(
        self,
        converted_current_message: BdnPerformanceStatsMessage,
        original_current_message: BdnPerformanceStatsMessage,
    ):
        self.assert_attributes_equal(
            converted_current_message,
            original_current_message,
            [
                "interval_start_time",
                "interval_end_time",
                "memory_utilization"
            ],
        )
        converted_node_stats = converted_current_message.node_stats()
        converted_blockchain_peer_endpoint, converted_single_node_stats = converted_node_stats.popitem()
        original_node_stats = original_current_message.node_stats()
        original_blockchain_peer_endpoint, original_single_node_stats = original_node_stats.popitem()
        self.assertEqual(
            converted_single_node_stats.new_blocks_received_from_blockchain_node,
            original_single_node_stats.new_blocks_received_from_blockchain_node
        )
        self.assertEqual(
            converted_single_node_stats.new_blocks_received_from_bdn,
            original_single_node_stats.new_blocks_received_from_bdn
        )
        self.assertEqual(
            converted_single_node_stats.new_tx_received_from_blockchain_node,
            original_single_node_stats.new_tx_received_from_blockchain_node
        )
        self.assertEqual(
            converted_single_node_stats.new_tx_received_from_bdn,
            original_single_node_stats.new_tx_received_from_bdn
        )
        self.assertEqual(
            converted_single_node_stats.new_blocks_seen,
            original_single_node_stats.new_blocks_seen
        )
        self.assertEqual(
            converted_single_node_stats.new_block_messages_from_blockchain_node,
            original_single_node_stats.new_block_messages_from_blockchain_node
        )
        self.assertEqual(
            converted_single_node_stats.new_block_announcements_from_blockchain_node,
            original_single_node_stats.new_block_announcements_from_blockchain_node
        )
        self.assertEqual(0, converted_single_node_stats.tx_sent_to_node)
        self.assertEqual(0, converted_single_node_stats.duplicate_tx_from_node)
