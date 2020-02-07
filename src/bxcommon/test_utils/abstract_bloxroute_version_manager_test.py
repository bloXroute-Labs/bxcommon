import time
import unittest
from abc import abstractmethod
from typing import TypeVar, cast, Generic, List, Any

from bxcommon import constants
from bxcommon.messages.abstract_message import AbstractMessage
from bxcommon.messages.bloxroute import protocol_version
from bxcommon.messages.bloxroute.abstract_bloxroute_message import (
    AbstractBloxrouteMessage,
)
from bxcommon.messages.bloxroute.ack_message import AckMessage
from bxcommon.messages.bloxroute.block_confirmation_message import (
    BlockConfirmationMessage,
)
from bxcommon.messages.bloxroute.blocks_short_ids_serializer import (
    BlockShortIds,
)
from bxcommon.messages.bloxroute.bloxroute_version_manager import (
    bloxroute_version_manager,
)
from bxcommon.messages.bloxroute.broadcast_message import BroadcastMessage
from bxcommon.messages.bloxroute.get_txs_message import GetTxsMessage
from bxcommon.messages.bloxroute.hello_message import HelloMessage
from bxcommon.messages.bloxroute.key_message import KeyMessage
from bxcommon.messages.bloxroute.notification_message import NotificationMessage
from bxcommon.messages.bloxroute.ping_message import PingMessage
from bxcommon.messages.bloxroute.pong_message import PongMessage
from bxcommon.messages.bloxroute.transaction_cleanup_message import (
    TransactionCleanupMessage,
)
from bxcommon.messages.bloxroute.tx_message import TxMessage
from bxcommon.messages.bloxroute.tx_service_sync_blocks_short_ids_message import (
    TxServiceSyncBlocksShortIdsMessage,
)
from bxcommon.messages.bloxroute.tx_service_sync_complete_message import (
    TxServiceSyncCompleteMessage,
)
from bxcommon.messages.bloxroute.tx_service_sync_req_message import (
    TxServiceSyncReqMessage,
)
from bxcommon.messages.bloxroute.tx_service_sync_txs_message import (
    TxServiceSyncTxsMessage,
)
from bxcommon.messages.bloxroute.txs_message import TxsMessage
from bxcommon.messages.bloxroute.txs_serializer import TxContentShortIds
from bxcommon.models.notification_code import NotificationCode
from bxcommon.models.quota_type_model import QuotaType
from bxcommon.models.transaction_info import TransactionInfo
from bxcommon.test_utils import helpers
from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.utils import nonce_generator

M1 = TypeVar("M1", bound=AbstractMessage)
M2 = TypeVar("M2", bound=AbstractMessage)
M3 = TypeVar("M3", bound=AbstractMessage)
M4 = TypeVar("M4", bound=AbstractMessage)
M5 = TypeVar("M5", bound=AbstractMessage)
M6 = TypeVar("M6", bound=AbstractMessage)
M7 = TypeVar("M7", bound=AbstractMessage)
M8 = TypeVar("M8", bound=AbstractMessage)
M9 = TypeVar("M9", bound=AbstractMessage)
M10 = TypeVar("M10", bound=AbstractMessage)
M11 = TypeVar("M11", bound=AbstractMessage)
M12 = TypeVar("M12", bound=AbstractMessage)
M13 = TypeVar("M13", bound=AbstractMessage)
M14 = TypeVar("M14", bound=AbstractMessage)
M15 = TypeVar("M15", bound=AbstractMessage)
M16 = TypeVar("M16", bound=AbstractMessage)


class AbstractBloxrouteVersionManagerTest(
    AbstractTestCase,
    Generic[
        M1, M2, M3, M4, M5, M6, M7, M8, M9, M10, M11, M12, M13, M14, M15, M16
    ],
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
        ]
    ):

    Replace X with the version number, and each updated message type
    accordingly.
    """

    NODE_ID = "02e5b506-7c6b-41ea-b0f9-19851f2a015b"
    NETWORK_NUMBER = 7

    def __init__(self, *args, **kwargs):
        # hack to avoid unit test discovery of this class
        super().__init__(*args, **kwargs)
        if self.__class__ != AbstractBloxrouteVersionManagerTest:
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
        return HelloMessage(
            protocol_version.PROTOCOL_VERSION, self.NETWORK_NUMBER, self.NODE_ID
        )

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
            QuotaType.PAID_DAILY_QUOTA,
            time.time(),
        )

    def gettxs_message(self) -> GetTxsMessage:
        return GetTxsMessage([i for i in range(1, 50)])

    def txs_message(self) -> TxsMessage:
        return TxsMessage(
            [
                TransactionInfo(
                    helpers.generate_object_hash(),
                    helpers.generate_bytearray(250),
                    i,
                )
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
                BlockShortIds(
                    helpers.generate_object_hash(),
                    [i for i in range(j * 10, j * 15)],
                )
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
                    [QuotaType.FREE_DAILY_QUOTA, QuotaType.PAID_DAILY_QUOTA],
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
            [i for i in range(100, 200)],
            [helpers.generate_object_hash() for _ in range(100)],
        )

    def txclnup_message(self) -> TransactionCleanupMessage:
        return TransactionCleanupMessage(
            self.NETWORK_NUMBER,
            self.NODE_ID,
            [i for i in range(50, 150)],
            [helpers.generate_object_hash() for _ in range(10)],
        )

    def notify_message(self) -> NotificationMessage:
        return NotificationMessage(
            NotificationCode.QUOTA_DEPLETED, str(helpers.generate_bytes(100))
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

    def old_txstart_message(
        self, original_message: TxServiceSyncReqMessage
    ) -> M10:
        return cast(M10, original_message)

    def old_txblock_message(
        self, original_message: TxServiceSyncBlocksShortIdsMessage
    ) -> M11:
        return cast(M11, original_message)

    def old_txtxs_message(
        self, original_message: TxServiceSyncTxsMessage
    ) -> M12:
        return cast(M12, original_message)

    def old_txdone_message(
        self, original_message: TxServiceSyncCompleteMessage
    ) -> M13:
        return cast(M13, original_message)

    def old_blkcnfrm_message(
        self, original_message: BlockConfirmationMessage
    ) -> M14:
        return cast(M14, original_message)

    def old_txclnup_message(
        self, original_message: TransactionCleanupMessage
    ) -> M15:
        return cast(M15, original_message)

    def old_notify_message(self, original_message: NotificationMessage) -> M16:
        return cast(M16, original_message)

    # </editor-fold>

    # <editor-fold desc="TEST CASES and COMPARISONS FUNCTIONS">

    # TODO: the rest of these needs to be filled out. Will do so in a follow-up
    # PR

    def compare_txclnup_current_to_old(
        self,
        converted_old_message: M15,
        original_old_message: M15,
    ):
        pass

    def compare_txclnup_old_to_current(
        self,
        converted_current_message: TransactionCleanupMessage,
        original_current_message: TransactionCleanupMessage,
    ):
        pass

    def test_txclnup_message(self):
        current_message = self.txclnup_message()
        old_message = self.old_txclnup_message(current_message)

        current_to_old_message = self._convert_to_older_version(
            current_message, old_message
        )
        old_to_current_message = cast(
            M15, self._convert_to_current_version(old_message, current_message)
        )

        self.compare_txclnup_current_to_old(current_to_old_message, old_message)
        self.compare_txclnup_old_to_current(old_to_current_message, current_message)

    def compare_notify_current_to_old(
        self,
        converted_old_message: M16,
        original_old_message: M16,
    ):
        pass

    def compare_notify_old_to_current(
        self,
        converted_current_message: NotificationMessage,
        original_current_message: NotificationMessage,
    ):
        pass

    def test_notify_message(self):
        current_message = self.notify_message()
        old_message = self.old_notify_message(current_message)

        current_to_old_message = self._convert_to_older_version(
            current_message, old_message
        )
        old_to_current_message = cast(
            M16, self._convert_to_current_version(old_message, current_message)
        )

        self.compare_notify_current_to_old(current_to_old_message, old_message)
        self.compare_notify_old_to_current(old_to_current_message, current_message)

    def compare_tx_current_to_old(
        self, converted_old_message: M6, original_old_message: M6,
    ):
        pass

    def compare_tx_old_to_current(
        self,
        converted_current_message: TxMessage,
        original_current_message: TxMessage,
    ):
        pass

    def test_tx_message(self):
        current_message = self.tx_message()
        old_message = self.old_tx_message(current_message)

        current_to_old_message = self._convert_to_older_version(
            current_message, old_message
        )
        old_to_current_message = cast(
            M16, self._convert_to_current_version(old_message, current_message),
        )

        self.compare_tx_current_to_old(current_to_old_message, old_message)
        self.compare_tx_old_to_current(old_to_current_message, current_message)

    def compare_txtxs_current_to_old(
        self, converted_old_message: M12, original_old_message: M12,
    ):
        pass

    def compare_txtxs_old_to_current(
        self,
        converted_current_message: TxServiceSyncTxsMessage,
        original_current_message: TxServiceSyncTxsMessage,
    ):
        pass

    def test_txtxs_message(self):
        current_message = self.txtxs_message()
        old_message = self.old_txtxs_message(current_message)

        current_to_old_message = self._convert_to_older_version(
            current_message, old_message
        )
        old_to_current_message = cast(
            M16, self._convert_to_current_version(old_message, current_message),
        )

        self.compare_txtxs_current_to_old(current_to_old_message, old_message)
        self.compare_txtxs_old_to_current(
            old_to_current_message, current_message
        )

    # </editor-fold>

    # <editor-fold desc="UTILITIES">

    def assert_attributes_equal(
        self,
        original_message: AbstractMessage,
        converted_message: AbstractMessage,
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
        self,
        converted_old_message: AbstractMessage,
        original_old_message: AbstractMessage,
    ):
        """
        This method is run on every message comparision, when comparing
        the current version converted to the older version.

        Override this if a change is made that affects every message.
        """
        self.assertEqual(
            constants.STARTING_SEQUENCE_BYTES,
            converted_old_message.rawbytes()[
                : constants.STARTING_SEQUENCE_BYTES_LEN
            ],
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
            converted_current_message.rawbytes()[
                : constants.STARTING_SEQUENCE_BYTES_LEN
            ],
        )
        self.assertEqual(
            original_current_message.msg_type(),
            converted_current_message.msg_type(),
        )
        self.assertEqual(
            original_current_message.payload_len(),
            converted_current_message.payload_len(),
        )
        self.assertEqual(
            original_current_message.get_control_flags(),
            converted_current_message.get_control_flags(),
        )

    def _convert_to_older_version(
        self,
        current_version_message: AbstractMessage,
        old_version_message: AbstractMessage,
    ) -> AbstractMessage:
        current_to_old_message = bloxroute_version_manager.convert_message_to_older_version(
            self.version_to_test(), current_version_message
        )
        self.compare_current_to_old(current_to_old_message, old_version_message)
        return current_to_old_message

    def _convert_to_current_version(
        self,
        old_version_message: AbstractMessage,
        current_version_message: AbstractBloxrouteMessage,
    ) -> AbstractMessage:
        old_to_current_message = bloxroute_version_manager.convert_message_from_older_version(
            self.version_to_test(), old_version_message
        )
        self.compare_old_to_current(
            old_to_current_message, current_version_message
        )
        return old_to_current_message

    def _invoke_and_get(self, message: AbstractMessage, attribute: str) -> Any:
        if not hasattr(message, attribute):
            raise ValueError(f"{attribute} does not exist on object: {message}")

        method = getattr(message, attribute)
        if not callable(method):
            raise ValueError(
                f"{attribute} is not " f"callable on object: {message}"
            )

        return method()

    # </editor-fold>


