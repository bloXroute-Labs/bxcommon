from typing import cast

from bxcommon.messages.abstract_internal_message import AbstractInternalMessage
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.tx_message import TxMessage
from bxcommon.messages.bloxroute.v17.tx_message_v17 import TxMessageV17
from bxcommon.messages.versioning.abstract_message_converter import AbstractMessageConverter
from bxcommon.models.transaction_flag import TransactionFlag


class _TxMessageConverterV17(AbstractMessageConverter):
    _MSG_TYPE_TO_OLD_MSG_CLASS_MAPPING = {
        BloxrouteMessageType.TRANSACTION: TxMessageV17
    }

    _MSG_TYPE_TO_NEW_MSG_CLASS_MAPPING = {
        BloxrouteMessageType.TRANSACTION: TxMessage
    }

    UNKNOWN_TRANSACTION_FLAGS = (
        TransactionFlag.LOCAL_REGION
        | TransactionFlag.PRIVATE_TX
        | TransactionFlag.TBD_2
        | TransactionFlag.TBD_3
        | TransactionFlag.TBD_4
        | TransactionFlag.TBD_5
    )
    INVERTED_UNKNOWN_TRANSACTION_FLAGS = (
        ~TransactionFlag.LOCAL_REGION
        & ~TransactionFlag.PRIVATE_TX
        & ~TransactionFlag.TBD_2
        & ~TransactionFlag.TBD_3
        & ~TransactionFlag.TBD_4
        & ~TransactionFlag.TBD_5
    )

    def convert_from_older_version(
        self, msg: AbstractInternalMessage
    ) -> AbstractInternalMessage:
        msg_type = msg.MESSAGE_TYPE

        if msg_type not in self._MSG_TYPE_TO_OLD_MSG_CLASS_MAPPING:
            raise ValueError(
                f"Tried to convert unexpected new "
                f"message type to v17: {msg_type}"
            )

        msg = cast(TxMessageV17, msg)

        tx_hash = msg.tx_hash()
        network_num = msg.network_num()
        source_id = msg.source_id()
        short_id = msg.short_id()
        tx_val = msg.tx_val()
        transaction_flag = msg.transaction_flag()
        ts = msg.timestamp()

        return TxMessage(
            message_hash=tx_hash,
            network_num=network_num,
            source_id=source_id,
            short_id=short_id,
            tx_val=tx_val,
            transaction_flag=transaction_flag,
            timestamp=ts
        )

    def convert_to_older_version(
        self, msg: AbstractInternalMessage
    ) -> AbstractInternalMessage:
        msg_type = msg.MESSAGE_TYPE

        if msg_type != TxMessage.MESSAGE_TYPE:
            raise ValueError(
                f"Tried to convert unexpected new "
                f"message type to v17: {msg_type}"
            )

        msg = cast(TxMessage, msg)
        transaction_flag = msg.transaction_flag()

        if self.UNKNOWN_TRANSACTION_FLAGS & transaction_flag:
            transaction_flag &= self.INVERTED_UNKNOWN_TRANSACTION_FLAGS

        return TxMessageV17(
            msg.message_hash(),
            msg.network_num(),
            msg.source_id(),
            msg.short_id(),
            msg.tx_val(),
            transaction_flag,
            int(msg.timestamp())
        )

    def convert_first_bytes_to_older_version(
        self, first_msg_bytes: memoryview
    ) -> memoryview:
        raise NotImplementedError

    def convert_first_bytes_from_older_version(
        self, first_msg_bytes: memoryview
    ) -> memoryview:
        raise NotImplementedError

    def convert_last_bytes_to_older_version(
        self, last_msg_bytes: memoryview
    ) -> memoryview:
        raise NotImplementedError

    def convert_last_bytes_from_older_version(
        self, last_msg_bytes: memoryview
    ) -> memoryview:
        raise NotImplementedError

    def get_message_size_change_to_older_version(self) -> int:
        return 0

    def get_message_size_change_from_older_version(self) -> int:
        return 0


tx_message_converter_v17 = _TxMessageConverterV17()
