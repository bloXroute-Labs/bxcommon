import time
import unittest
from abc import abstractmethod
from datetime import datetime
from typing import TypeVar, cast, Generic, List, Any

from bxcommon import constants
from bxcommon.messages.bloxroute import protocol_version
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.messages.bloxroute.ack_message import AckMessage
from bxcommon.messages.bloxroute.bdn_performance_stats_message import BdnPerformanceStatsMessage
from bxcommon.messages.bloxroute.block_confirmation_message import BlockConfirmationMessage
from bxcommon.messages.bloxroute.blocks_short_ids_serializer import BlockShortIds
from bxcommon.messages.bloxroute.bloxroute_version_manager import bloxroute_version_manager
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
from bxcommon.messages.bloxroute.txs_serializer import TxContentShortIds
from bxcommon.models.broadcast_message_type import BroadcastMessageType
from bxcommon.models.notification_code import NotificationCode
from bxcommon.models.transaction_flag import TransactionFlag
from bxcommon.models.transaction_info import TransactionInfo
from bxcommon.test_utils import helpers
from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.utils import nonce_generator

M1 = TypeVar("M1", bound=AbstractBloxrouteMessage)
M2 = TypeVar("M2", bound=AbstractBloxrouteMessage)
M3 = TypeVar("M3", bound=AbstractBloxrouteMessage)
M4 = TypeVar("M4", bound=AbstractBloxrouteMessage)
M5 = TypeVar("M5", bound=AbstractBloxrouteMessage)
M6 = TypeVar("M6", bound=AbstractBloxrouteMessage)
M7 = TypeVar("M7", bound=AbstractBloxrouteMessage)
M8 = TypeVar("M8", bound=AbstractBloxrouteMessage)
M9 = TypeVar("M9", bound=AbstractBloxrouteMessage)
M10 = TypeVar("M10", bound=AbstractBloxrouteMessage)
M11 = TypeVar("M11", bound=AbstractBloxrouteMessage)
M12 = TypeVar("M12", bound=AbstractBloxrouteMessage)
M13 = TypeVar("M13", bound=AbstractBloxrouteMessage)
M14 = TypeVar("M14", bound=AbstractBloxrouteMessage)
M15 = TypeVar("M15", bound=AbstractBloxrouteMessage)
M16 = TypeVar("M16", bound=AbstractBloxrouteMessage)
M17 = TypeVar("M17", bound=AbstractBloxrouteMessage)


# pylint: disable=too-many-public-methods
class AbstractBloxrouteVersionManagerTest(
    AbstractTestCase,
    Generic[M1, M2, M3, M4, M5, M6, M7, M8, M9, M10, M11, M12, M13, M14, M15, M16, M17],
):
    """
    Template to get you started:

    class BloxrouteTxVersionManagerVXTest(
        AbstractVersionManagerTest[
            HelloMessage,
            AckMessage,
            PingMessage,
            PongMessage,
            BroadcastMessage,
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

    Replace X with the version number, and each updated message type
    accordingly.
    """

    NODE_ID = "02e5b506-7c6b-41ea-b0f9-19851f2a015b"
    NETWORK_NUMBER = 7
    BROADCAST_TYPE = BroadcastMessageType.BLOCK

    def __init__(self, *args, **kwargs) -> None:
        # hack to avoid unit test discovery of this class
        super().__init__(*args, **kwargs)
        if self.__class__ != AbstractBloxrouteVersionManagerTest:
            # pylint: disable=no-value-for-parameter
            # pyre-ignore[16]
            self.run = unittest.TestCase.run.__get__(self, self.__class__)
        else:
            self.run = lambda self, *args, **kwargs: None

    @abstractmethod
    def version_to_test(self) -> int:
        pass

    # <editor-fold desc="CURRENT DEFINITIONS" defaultstate="collapsed">

    # Functions creating a current, up-to-date version of each message type
    # in our protocol, with all fields populated.
    #
    # Update this section if you ever add new fields or change the types of
    # our message classes.

    def hello_message(self) -> HelloMessage:
        return HelloMessage(protocol_version.PROTOCOL_VERSION, self.NETWORK_NUMBER, self.NODE_ID)

    def ack_message(self) -> AckMessage:
        return AckMessage()

    def ping_message(self) -> PingMessage:
        return PingMessage(nonce_generator.get_nonce())

    def pong_message(self) -> PongMessage:
        return PongMessage(nonce_generator.get_nonce())

    def broadcast_message(self) -> BroadcastMessage:
        return BroadcastMessage(
            helpers.generate_object_hash(),
            self.NETWORK_NUMBER,
            self.NODE_ID,
            self.BROADCAST_TYPE,
            False,
            helpers.generate_bytearray(500),
        )

    def tx_message(self) -> TxMessage:
        return TxMessage(
            helpers.generate_object_hash(),
            self.NETWORK_NUMBER,
            self.NODE_ID,
            50,
            helpers.generate_bytearray(250),
            TransactionFlag.PAID_TX,
            time.time(),
        )

    def gettxs_message(self) -> GetTxsMessage:
        return GetTxsMessage(list(range(1, 50)))

    def txs_message(self) -> TxsMessage:
        return TxsMessage(
            [
                TransactionInfo(helpers.generate_object_hash(), helpers.generate_bytearray(250), i,)
                for i in range(1, 10)
            ]
        )

    def key_message(self) -> KeyMessage:
        return KeyMessage(
            helpers.generate_object_hash(),
            self.NETWORK_NUMBER,
            self.NODE_ID,
            helpers.generate_bytearray(32),
        )

    def txstart_message(self) -> TxServiceSyncReqMessage:
        return TxServiceSyncReqMessage(self.NETWORK_NUMBER)

    def txblock_message(self) -> TxServiceSyncBlocksShortIdsMessage:
        return TxServiceSyncBlocksShortIdsMessage(
            self.NETWORK_NUMBER,
            [
                BlockShortIds(helpers.generate_object_hash(), list(range(j * 10, j * 15)),)
                for j in range(2, 20)
            ],
        )

    def txtxs_message(self) -> TxServiceSyncTxsMessage:
        return TxServiceSyncTxsMessage(
            self.NETWORK_NUMBER,
            [
                TxContentShortIds(
                    helpers.generate_object_hash(),
                    helpers.generate_bytearray(250),
                    [2, 3],
                    [TransactionFlag.NO_FLAGS, TransactionFlag.PAID_TX],
                )
            ],
        )

    def txdone_message(self) -> TxServiceSyncCompleteMessage:
        return TxServiceSyncCompleteMessage(self.NETWORK_NUMBER)

    def blkcnfrm_message(self) -> BlockConfirmationMessage:
        return BlockConfirmationMessage(
            helpers.generate_object_hash(),
            self.NETWORK_NUMBER,
            self.NODE_ID,
            list(range(100, 200)),
            [helpers.generate_object_hash() for _ in range(100)],
        )

    def txclnup_message(self) -> TransactionCleanupMessage:
        return TransactionCleanupMessage(
            self.NETWORK_NUMBER,
            self.NODE_ID,
            list(range(50, 150)),
            [helpers.generate_object_hash() for _ in range(10)],
        )

    def notify_message(self) -> NotificationMessage:
        return NotificationMessage(
            NotificationCode.QUOTA_FILL_STATUS, str(helpers.generate_bytes(100))
        )

    def bdn_performance_stats_message(self) -> BdnPerformanceStatsMessage:
        node_stats = {}
        helpers.add_stats_to_node_stats(
            node_stats,
            "127.0.0.1", 8001,
            20, 30, 40, 50, 10, 10, 20, 100, 50
        )
        return BdnPerformanceStatsMessage(
            datetime.utcnow(),
            datetime.utcnow(),
            100,
            node_stats
        )

    # </editor-fold>

    # <editor-fold desc="OLD DEFINITIONS" defaultstate="collapsed">

    # Functions for creating message of previous versions.
    # These are intended to be overridden by subclass test cases.

    def old_hello_message(self, original_message: HelloMessage) -> M1:
        return cast(M1, original_message)

    def old_ack_message(self, original_message: AckMessage) -> M2:
        return cast(M2, original_message)

    def old_ping_message(self, original_message: PingMessage) -> M3:
        return cast(M3, original_message)

    def old_pong_message(self, original_message: PongMessage) -> M4:
        return cast(M4, original_message)

    def old_broadcast_message(self, original_message: BroadcastMessage) -> M5:
        return cast(M5, original_message)

    def old_tx_message(self, original_message: TxMessage) -> M6:
        return cast(M6, original_message)

    def old_gettxs_message(self, original_message: GetTxsMessage) -> M7:
        return cast(M7, original_message)

    def old_txs_message(self, original_message: TxsMessage) -> M8:
        return cast(M8, original_message)

    def old_key_message(self, original_message: KeyMessage) -> M9:
        return cast(M9, original_message)

    def old_txstart_message(self, original_message: TxServiceSyncReqMessage) -> M10:
        return cast(M10, original_message)

    def old_txblock_message(self, original_message: TxServiceSyncBlocksShortIdsMessage) -> M11:
        return cast(M11, original_message)

    def old_txtxs_message(self, original_message: TxServiceSyncTxsMessage) -> M12:
        return cast(M12, original_message)

    def old_txdone_message(self, original_message: TxServiceSyncCompleteMessage) -> M13:
        return cast(M13, original_message)

    def old_blkcnfrm_message(self, original_message: BlockConfirmationMessage) -> M14:
        return cast(M14, original_message)

    def old_txclnup_message(self, original_message: TransactionCleanupMessage) -> M15:
        return cast(M15, original_message)

    def old_notify_message(self, original_message: NotificationMessage) -> M16:
        return cast(M16, original_message)

    def old_bdn_performance_stats_message(self, original_message: BdnPerformanceStatsMessage) -> M17:
        return cast(M17, original_message)

    # </editor-fold>

    # <editor-fold desc="TEST CASES and COMPARISONS FUNCTIONS">

    def compare_hello_current_to_old(
        self, converted_old_message: M1, original_old_message: M1,
    ):
        self.assertEqual(
            original_old_message.rawbytes(), converted_old_message.rawbytes(),
        )

    def compare_hello_old_to_current(
        self, converted_current_message: HelloMessage, original_current_message: HelloMessage,
    ):
        self.assertEqual(
            original_current_message.rawbytes(), converted_current_message.rawbytes(),
        )

    def test_hello_message(self):
        current_message = self.hello_message()
        old_message = self.old_hello_message(current_message)

        current_to_old_message = self._convert_to_older_version(current_message, old_message)
        old_to_current_message = cast(
            M1, self._convert_to_current_version(old_message, current_message)
        )

        self.compare_hello_current_to_old(current_to_old_message, old_message)
        self.compare_hello_old_to_current(old_to_current_message, current_message)

    def compare_ack_current_to_old(
        self, converted_old_message: M2, original_old_message: M2,
    ):
        self.assertEqual(
            original_old_message.rawbytes(), converted_old_message.rawbytes(),
        )

    def compare_ack_old_to_current(
        self, converted_current_message: AckMessage, original_current_message: AckMessage,
    ):
        self.assertEqual(
            original_current_message.rawbytes(), converted_current_message.rawbytes(),
        )

    def test_ack_message(self):
        current_message = self.ack_message()
        old_message = self.old_ack_message(current_message)

        current_to_old_message = self._convert_to_older_version(current_message, old_message)
        old_to_current_message = cast(
            M2, self._convert_to_current_version(old_message, current_message)
        )

        self.compare_ack_current_to_old(current_to_old_message, old_message)
        self.compare_ack_old_to_current(old_to_current_message, current_message)

    def compare_ping_current_to_old(
        self, converted_old_message: M3, original_old_message: M3,
    ):
        self.assertEqual(
            original_old_message.rawbytes(), converted_old_message.rawbytes(),
        )

    def compare_ping_old_to_current(
        self, converted_current_message: PingMessage, original_current_message: PingMessage,
    ):
        self.assertEqual(
            original_current_message.rawbytes(), converted_current_message.rawbytes(),
        )

    def test_ping_message(self):
        current_message = self.ping_message()
        old_message = self.old_ping_message(current_message)

        current_to_old_message = self._convert_to_older_version(current_message, old_message)
        old_to_current_message = cast(
            M3, self._convert_to_current_version(old_message, current_message)
        )

        self.compare_ping_current_to_old(current_to_old_message, old_message)
        self.compare_ping_old_to_current(old_to_current_message, current_message)

    def compare_pong_current_to_old(
        self, converted_old_message: M4, original_old_message: M4,
    ):
        self.assertEqual(
            original_old_message.rawbytes(), converted_old_message.rawbytes(),
        )

    def compare_pong_old_to_current(
        self, converted_current_message: PongMessage, original_current_message: PongMessage,
    ):
        self.assertEqual(
            original_current_message.rawbytes(), converted_current_message.rawbytes(),
        )

    def test_pong_message(self):
        current_message = self.pong_message()
        old_message = self.old_pong_message(current_message)

        current_to_old_message = self._convert_to_older_version(current_message, old_message)
        old_to_current_message = cast(
            M4, self._convert_to_current_version(old_message, current_message)
        )

        self.compare_pong_current_to_old(current_to_old_message, old_message)
        self.compare_pong_old_to_current(old_to_current_message, current_message)

    def compare_broadcast_current_to_old(
        self, converted_old_message: M5, original_old_message: M5,
    ):
        self.assertEqual(
            original_old_message.rawbytes(), converted_old_message.rawbytes(),
        )

    def compare_broadcast_old_to_current(
        self,
        converted_current_message: BroadcastMessage,
        original_current_message: BroadcastMessage,
    ):
        self.assertEqual(
            original_current_message.rawbytes(), converted_current_message.rawbytes(),
        )

    def test_broadcast_message(self):
        current_message = self.broadcast_message()
        old_message = self.old_broadcast_message(current_message)

        current_to_old_message = self._convert_to_older_version(current_message, old_message)
        old_to_current_message = cast(
            M5, self._convert_to_current_version(old_message, current_message)
        )

        self.compare_broadcast_current_to_old(current_to_old_message, old_message)
        self.compare_broadcast_old_to_current(old_to_current_message, current_message)

    def compare_tx_current_to_old(
        self, converted_old_message: M6, original_old_message: M6,
    ):
        self.assertEqual(
            original_old_message.rawbytes(), converted_old_message.rawbytes(),
        )

    def compare_tx_old_to_current(
        self, converted_current_message: TxMessage, original_current_message: TxMessage,
    ):
        self.assertEqual(
            original_current_message.rawbytes(), converted_current_message.rawbytes(),
        )

    def test_tx_message(self):
        current_message = self.tx_message()
        old_message = self.old_tx_message(current_message)

        current_to_old_message = self._convert_to_older_version(current_message, old_message)
        old_to_current_message = cast(
            M6, self._convert_to_current_version(old_message, current_message)
        )

        self.compare_tx_current_to_old(current_to_old_message, old_message)
        self.compare_tx_old_to_current(old_to_current_message, current_message)

    def compare_gettxs_current_to_old(
        self, converted_old_message: M7, original_old_message: M7,
    ):
        self.assertEqual(
            original_old_message.rawbytes(), converted_old_message.rawbytes(),
        )

    def compare_gettxs_old_to_current(
        self, converted_current_message: GetTxsMessage, original_current_message: GetTxsMessage,
    ):
        self.assertEqual(
            original_current_message.rawbytes(), converted_current_message.rawbytes(),
        )

    def test_gettxs_message(self):
        current_message = self.gettxs_message()
        old_message = self.old_gettxs_message(current_message)

        current_to_old_message = self._convert_to_older_version(current_message, old_message)
        old_to_current_message = cast(
            M7, self._convert_to_current_version(old_message, current_message)
        )

        self.compare_gettxs_current_to_old(current_to_old_message, old_message)
        self.compare_gettxs_old_to_current(old_to_current_message, current_message)

    def compare_txs_current_to_old(
        self, converted_old_message: M8, original_old_message: M8,
    ):
        self.assertEqual(
            original_old_message.rawbytes(), converted_old_message.rawbytes(),
        )

    def compare_txs_old_to_current(
        self, converted_current_message: TxsMessage, original_current_message: TxsMessage,
    ):
        self.assertEqual(
            original_current_message.rawbytes(), converted_current_message.rawbytes(),
        )

    def test_txs_message(self):
        current_message = self.txs_message()
        old_message = self.old_txs_message(current_message)

        current_to_old_message = self._convert_to_older_version(current_message, old_message)
        old_to_current_message = cast(
            M8, self._convert_to_current_version(old_message, current_message)
        )

        self.compare_txs_current_to_old(current_to_old_message, old_message)
        self.compare_txs_old_to_current(old_to_current_message, current_message)

    def compare_key_current_to_old(
        self, converted_old_message: M9, original_old_message: M9,
    ):
        self.assertEqual(
            original_old_message.rawbytes(), converted_old_message.rawbytes(),
        )

    def compare_key_old_to_current(
        self, converted_current_message: KeyMessage, original_current_message: KeyMessage,
    ):
        self.assertEqual(
            original_current_message.rawbytes(), converted_current_message.rawbytes(),
        )

    def test_key_message(self):
        current_message = self.key_message()
        old_message = self.old_key_message(current_message)

        current_to_old_message = self._convert_to_older_version(current_message, old_message)
        old_to_current_message = cast(
            M9, self._convert_to_current_version(old_message, current_message)
        )

        self.compare_key_current_to_old(current_to_old_message, old_message)
        self.compare_key_old_to_current(old_to_current_message, current_message)

    def compare_txstart_current_to_old(
        self, converted_old_message: M10, original_old_message: M10,
    ):
        self.assertEqual(
            original_old_message.rawbytes(), converted_old_message.rawbytes(),
        )

    def compare_txstart_old_to_current(
        self,
        converted_current_message: TxServiceSyncReqMessage,
        original_current_message: TxServiceSyncReqMessage,
    ):
        self.assertEqual(
            original_current_message.rawbytes(), converted_current_message.rawbytes(),
        )

    def test_txstart_message(self):
        current_message = self.txstart_message()
        old_message = self.old_txstart_message(current_message)

        current_to_old_message = self._convert_to_older_version(current_message, old_message)
        old_to_current_message = cast(
            M10, self._convert_to_current_version(old_message, current_message)
        )

        self.compare_txstart_current_to_old(current_to_old_message, old_message)
        self.compare_txstart_old_to_current(old_to_current_message, current_message)

    def compare_txblock_current_to_old(
        self, converted_old_message: M11, original_old_message: M11,
    ):
        self.assertEqual(
            original_old_message.rawbytes(), converted_old_message.rawbytes(),
        )

    def compare_txblock_old_to_current(
        self,
        converted_current_message: TxServiceSyncBlocksShortIdsMessage,
        original_current_message: TxServiceSyncBlocksShortIdsMessage,
    ):
        self.assertEqual(
            original_current_message.rawbytes(), converted_current_message.rawbytes(),
        )

    def test_txblock_message(self):
        current_message = self.txblock_message()
        old_message = self.old_txblock_message(current_message)

        current_to_old_message = self._convert_to_older_version(current_message, old_message)
        old_to_current_message = cast(
            M11, self._convert_to_current_version(old_message, current_message)
        )

        self.compare_txblock_current_to_old(current_to_old_message, old_message)
        self.compare_txblock_old_to_current(old_to_current_message, current_message)

    def compare_txtxs_current_to_old(
        self, converted_old_message: M12, original_old_message: M12,
    ):
        self.assertEqual(
            original_old_message.rawbytes(), converted_old_message.rawbytes(),
        )

    def compare_txtxs_old_to_current(
        self,
        converted_current_message: TxServiceSyncTxsMessage,
        original_current_message: TxServiceSyncTxsMessage,
    ):
        self.assertEqual(
            original_current_message.rawbytes(), converted_current_message.rawbytes(),
        )

    def test_txtxs_message(self):
        current_message = self.txtxs_message()
        old_message = self.old_txtxs_message(current_message)

        current_to_old_message = self._convert_to_older_version(current_message, old_message)
        old_to_current_message = cast(
            M12, self._convert_to_current_version(old_message, current_message)
        )

        self.compare_txtxs_current_to_old(current_to_old_message, old_message)
        self.compare_txtxs_old_to_current(old_to_current_message, current_message)

    def compare_txdone_current_to_old(
        self, converted_old_message: M13, original_old_message: M13,
    ):
        self.assertEqual(
            original_old_message.rawbytes(), converted_old_message.rawbytes(),
        )

    def compare_txdone_old_to_current(
        self,
        converted_current_message: TxServiceSyncCompleteMessage,
        original_current_message: TxServiceSyncCompleteMessage,
    ):
        self.assertEqual(
            original_current_message.rawbytes(), converted_current_message.rawbytes(),
        )

    def test_txdone_message(self):
        current_message = self.txdone_message()
        old_message = self.old_txdone_message(current_message)

        current_to_old_message = self._convert_to_older_version(current_message, old_message)
        old_to_current_message = cast(
            M13, self._convert_to_current_version(old_message, current_message)
        )

        self.compare_txdone_current_to_old(current_to_old_message, old_message)
        self.compare_txdone_old_to_current(old_to_current_message, current_message)

    def compare_blkcnfrm_current_to_old(
        self, converted_old_message: M14, original_old_message: M14,
    ):
        self.assertEqual(
            original_old_message.rawbytes(), converted_old_message.rawbytes(),
        )

    def compare_blkcnfrm_old_to_current(
        self,
        converted_current_message: BlockConfirmationMessage,
        original_current_message: BlockConfirmationMessage,
    ):
        self.assertEqual(
            original_current_message.rawbytes(), converted_current_message.rawbytes(),
        )

    def test_blkcnfrm_message(self):
        current_message = self.blkcnfrm_message()
        old_message = self.old_blkcnfrm_message(current_message)

        current_to_old_message = self._convert_to_older_version(current_message, old_message)
        old_to_current_message = cast(
            M14, self._convert_to_current_version(old_message, current_message)
        )

        self.compare_blkcnfrm_current_to_old(current_to_old_message, old_message)
        self.compare_blkcnfrm_old_to_current(old_to_current_message, current_message)

    def compare_txclnup_current_to_old(
        self, converted_old_message: M15, original_old_message: M15,
    ):
        self.assertEqual(
            original_old_message.rawbytes(), converted_old_message.rawbytes(),
        )

    def compare_txclnup_old_to_current(
        self,
        converted_current_message: TransactionCleanupMessage,
        original_current_message: TransactionCleanupMessage,
    ):
        self.assertEqual(
            original_current_message.rawbytes(), converted_current_message.rawbytes(),
        )

    def test_txclnup_message(self):
        current_message = self.txclnup_message()
        old_message = self.old_txclnup_message(current_message)

        current_to_old_message = self._convert_to_older_version(current_message, old_message)
        old_to_current_message = cast(
            M15, self._convert_to_current_version(old_message, current_message)
        )

        self.compare_txclnup_current_to_old(current_to_old_message, old_message)
        self.compare_txclnup_old_to_current(old_to_current_message, current_message)

    def compare_notify_current_to_old(
        self, converted_old_message: M16, original_old_message: M16,
    ):
        self.assertEqual(
            original_old_message.rawbytes(), converted_old_message.rawbytes(),
        )

    def compare_notify_old_to_current(
        self,
        converted_current_message: NotificationMessage,
        original_current_message: NotificationMessage,
    ):
        self.assertEqual(
            original_current_message.rawbytes(), converted_current_message.rawbytes(),
        )

    def test_notify_message(self):
        current_message = self.notify_message()
        old_message = self.old_notify_message(current_message)

        current_to_old_message = self._convert_to_older_version(current_message, old_message)
        old_to_current_message = cast(
            M16, self._convert_to_current_version(old_message, current_message)
        )

        self.compare_notify_current_to_old(current_to_old_message, old_message)
        self.compare_notify_old_to_current(old_to_current_message, current_message)

    def compare_bdn_performance_stats_current_to_old(
        self, converted_old_message: M17, original_old_message: M17,
    ):
        self.assertEqual(
            original_old_message.rawbytes(), converted_old_message.rawbytes(),
        )

    def compare_bdn_performance_stats_old_to_current(
            self,
            converted_current_message: BdnPerformanceStatsMessage,
            original_current_message: BdnPerformanceStatsMessage,
    ):
        self.assertEqual(
            original_current_message.rawbytes(), converted_current_message.rawbytes(),
        )

    def test_bdn_performance_stats_message(self):
        current_message = self.bdn_performance_stats_message()
        old_message = self.old_bdn_performance_stats_message(current_message)

        old_to_current_message = cast(
            M16, self._convert_to_current_version(old_message, current_message)
        )
        self.compare_bdn_performance_stats_old_to_current(old_to_current_message, current_message)

    # </editor-fold>

    # <editor-fold desc="UTILITIES">

    def assert_attributes_equal(
        self,
        original_message: AbstractBloxrouteMessage,
        converted_message: AbstractBloxrouteMessage,
        attributes: List[str],
    ):
        for attribute in attributes:
            self.assertEqual(
                self._invoke_and_get(original_message, attribute),
                self._invoke_and_get(converted_message, attribute),
                f"Attribute {attribute} did not match!",
            )

    # noinspection PyUnresolvedReferences
    def compare_current_to_old(
        self, converted_old_message: AbstractBloxrouteMessage, original_old_message: AbstractBloxrouteMessage,
    ):
        """
        This method is run on every message comparison, when comparing
        the current version converted to the older version.

        Override this if a change is made that affects every message.
        """
        self.assertEqual(
            constants.STARTING_SEQUENCE_BYTES,
            converted_old_message.rawbytes()[: constants.STARTING_SEQUENCE_BYTES_LEN],
        )
        self.assertEqual(
            original_old_message.msg_type(), converted_old_message.msg_type(),
        )
        self.assertEqual(
            original_old_message.payload_len(),
            converted_old_message.payload_len(),
        )
        self.assertEqual(
            original_old_message.get_control_flags(),
            converted_old_message.get_control_flags(),
        )

    def compare_old_to_current(
        self,
        converted_current_message: AbstractBloxrouteMessage,
        original_current_message: AbstractBloxrouteMessage,
    ):
        """
        This method is run on every message comparision, when comparing
        the old version converted to the current version.

        Override this if a change is made that affects every message.
        """
        self.assertEqual(
            constants.STARTING_SEQUENCE_BYTES,
            converted_current_message.rawbytes()[: constants.STARTING_SEQUENCE_BYTES_LEN],
        )
        self.assertEqual(
            original_current_message.msg_type(), converted_current_message.msg_type(),
        )
        self.assertEqual(
            original_current_message.payload_len(), converted_current_message.payload_len(),
        )
        self.assertEqual(
            original_current_message.get_control_flags(),
            converted_current_message.get_control_flags(),
        )

    def _convert_to_older_version(
        self, current_version_message: AbstractBloxrouteMessage, old_version_message: AbstractBloxrouteMessage,
    ) -> AbstractBloxrouteMessage:
        current_to_old_message = bloxroute_version_manager.convert_message_to_older_version(
            self.version_to_test(), current_version_message
        )
        self.compare_current_to_old(current_to_old_message, old_version_message)
        return current_to_old_message

    def _convert_to_current_version(
        self,
        old_version_message: AbstractBloxrouteMessage,
        current_version_message: AbstractBloxrouteMessage,
    ) -> AbstractBloxrouteMessage:
        old_to_current_message = bloxroute_version_manager.convert_message_from_older_version(
            self.version_to_test(), old_version_message
        )
        self.compare_old_to_current(old_to_current_message, current_version_message)
        return old_to_current_message

    def _invoke_and_get(self, message: AbstractBloxrouteMessage, attribute: str) -> Any:
        if not hasattr(message, attribute):
            raise ValueError(f"{attribute} does not exist on object: {message}")

        method = getattr(message, attribute)
        if not callable(method):
            raise ValueError(f"{attribute} is not " f"callable on object: {message}")

        return method()

    # </editor-fold>
