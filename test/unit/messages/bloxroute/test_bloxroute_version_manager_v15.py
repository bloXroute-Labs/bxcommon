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
from bxcommon.messages.bloxroute.v14.bdn_performance_stats_message_v14 import BdnPerformanceStatsMessageV14
from bxcommon.messages.bloxroute.v15.tx_service_sync_txs_message_v15 import TxServiceSyncTxsMessageV15
from bxcommon.messages.bloxroute.txs_message import TxsMessage
from bxcommon.messages.bloxroute.v15.tx_message_v15 import TxMessageV15
from bxcommon.messages.bloxroute.v15.txs_serializer_v15 import TxContentShortIdsV15
from bxcommon.models.transaction_flag import TransactionFlag
from bxcommon.test_utils.abstract_bloxroute_version_manager_test import AbstractBloxrouteVersionManagerTest


class BloxrouteVersionManagerV15Test(
    AbstractBloxrouteVersionManagerTest[
        HelloMessage,
        AckMessage,
        PingMessage,
        PongMessage,
        BroadcastMessage,
        TxMessageV15,
        GetTxsMessage,
        TxsMessage,
        KeyMessage,
        TxServiceSyncReqMessage,
        TxServiceSyncBlocksShortIdsMessage,
        TxServiceSyncTxsMessageV15,
        TxServiceSyncCompleteMessage,
        BlockConfirmationMessage,
        TransactionCleanupMessage,
        NotificationMessage,
        BdnPerformanceStatsMessageV14,
    ]
):

    def version_to_test(self) -> int:
        return 15

    def old_tx_message(self, original_message: TxMessage) -> TxMessageV15:
        return TxMessageV15(
            original_message.message_hash(),
            original_message.network_num(),
            original_message.source_id(),
            original_message.short_id(),
            original_message.tx_val(),
            original_message.transaction_flag().get_quota_type(),
        )

    def old_txtxs_message(
        self, original_message: TxServiceSyncTxsMessage
    ) -> TxServiceSyncTxsMessageV15:
        return TxServiceSyncTxsMessageV15(
            original_message.network_num(),
            [
                TxContentShortIdsV15(
                    tx_content_short_ids.tx_hash,
                    tx_content_short_ids.tx_content,
                    tx_content_short_ids.short_ids,
                    [short_id_flag.get_quota_type() for short_id_flag in tx_content_short_ids.short_id_flags]
                )
                for tx_content_short_ids in original_message.txs_content_short_ids()
            ],
        )

    def compare_tx_current_to_old(
        self,
        converted_old_message: TxMessageV15,
        original_old_message: TxMessageV15,
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
            ]
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
            ],
        )
        self.assertEqual(
            original_current_message.transaction_flag(),
            converted_current_message.transaction_flag()
        )

    def compare_txtxs_current_to_old(
        self,
        converted_old_message: TxServiceSyncTxsMessageV15,
        original_old_message: TxServiceSyncTxsMessageV15,
    ):
        self.assert_attributes_equal(
            original_old_message,
            converted_old_message,
            ["network_num", "txs_content_short_ids"],
        )

    def compare_txtxs_old_to_current(
        self,
        converted_current_message: TxServiceSyncTxsMessage,
        original_current_message: TxServiceSyncTxsMessage,
    ):
        self.assert_attributes_equal(
            original_current_message, converted_current_message, ["network_num"]
        )
        original_txs_content_short_ids = (
            original_current_message.txs_content_short_ids()
        )
        converted_txs_content_short_ids = (
            converted_current_message.txs_content_short_ids()
        )
        self.assertEqual(
            len(original_txs_content_short_ids),
            len(converted_txs_content_short_ids),
        )
        for i in range(len(original_txs_content_short_ids)):
            original = original_txs_content_short_ids[i]
            converted = converted_txs_content_short_ids[i]

            self.assertEqual(original.tx_hash, converted.tx_hash)
            self.assertEqual(original.tx_content, converted.tx_content)
            self.assertEqual(original.short_ids, converted.short_ids)
            self.assertEqual(
                [TransactionFlag(short_id_flag.value) for short_id_flag in converted.short_id_flags],
                converted.short_id_flags,
            )

    def old_bdn_performance_stats_message(
        self, original_message: BdnPerformanceStatsMessage
    ) -> BdnPerformanceStatsMessageV14:
        _, single_node_stats = next(iter(original_message.node_stats().items()))
        return BdnPerformanceStatsMessageV14(
            original_message.interval_start_time(),
            original_message.interval_end_time(),
            single_node_stats.new_blocks_received_from_blockchain_node,
            single_node_stats.new_blocks_received_from_bdn,
            single_node_stats.new_tx_received_from_blockchain_node,
            single_node_stats.new_tx_received_from_bdn,
            original_message.memory_utilization()
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
        self.assertEqual(0, converted_single_node_stats.new_blocks_seen)
        self.assertEqual(0, converted_single_node_stats.new_block_messages_from_blockchain_node)
        self.assertEqual(0, converted_single_node_stats.new_block_announcements_from_blockchain_node)
        self.assertEqual(0, converted_single_node_stats.tx_sent_to_node)
        self.assertEqual(0, converted_single_node_stats.duplicate_tx_from_node)
