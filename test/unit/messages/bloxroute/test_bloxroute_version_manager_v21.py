from bxcommon.messages.bloxroute.ack_message import AckMessage
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
from bxcommon.messages.bloxroute.v18.bdn_performance_stats_message_v18 import BdnPerformanceStatsMessageV18
from bxcommon.messages.bloxroute.v21.tx_message_v21 import TxMessageV21
from bxcommon.test_utils.abstract_bloxroute_version_manager_test import AbstractBloxrouteVersionManagerTest


class BloxrouteVersionManagerV21Test(
    AbstractBloxrouteVersionManagerTest[
        HelloMessage,
        AckMessage,
        PingMessage,
        PongMessage,
        BroadcastMessage,
        TxMessageV21,
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
        BdnPerformanceStatsMessageV18
    ]
):

    def version_to_test(self) -> int:
        return 21

    def old_tx_message(self, original_message: TxMessage) -> TxMessageV21:
        return TxMessageV21(
            original_message.message_hash(),
            original_message.network_num(),
            original_message.source_id(),
            original_message.short_id(),
            original_message.tx_val(),
            original_message.transaction_flag(),
            original_message.timestamp()
        )

    def compare_tx_current_to_old(
        self,
        converted_old_message: TxMessageV21,
        original_old_message: TxMessageV21,
    ):
        self.assert_attributes_equal(
            original_old_message,
            converted_old_message,
            [
                "message_hash",
                "tx_val",
                "source_id",
                "network_num",
                "transaction_flag",
                "timestamp",
            ],
        )

    def compare_tx_old_to_current(
        self,
        converted_current_message: TxMessage,
        original_current_message: TxMessage,
    ):
        self.assert_attributes_equal(
            converted_current_message,
            original_current_message,
            [
                "message_hash",
                "tx_val",
                "source_id",
                "network_num",
                "transaction_flag",
                "timestamp",
                "account_id"
            ],
        )
