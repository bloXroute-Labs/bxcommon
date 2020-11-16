from typing import cast

from bxcommon.messages.abstract_internal_message import AbstractInternalMessage
from bxcommon.messages.bloxroute.tx_message import TxMessage
from bxcommon.messages.versioning.abstract_message_converter import AbstractMessageConverter
from bxcommon.models.transaction_flag import TransactionFlag


class _TxMessageConverterV17(AbstractMessageConverter):
    def convert_from_older_version(
        self, msg: AbstractInternalMessage
    ) -> AbstractInternalMessage:
        # message change is only in TransactionFlag attribute
        # older versions will simply never has this attribute set and will not need changes
        return msg

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

        if TransactionFlag.CEN_ENABLED not in transaction_flag:
            return msg

        transaction_flag &= ~TransactionFlag.CEN_ENABLED

        return TxMessage(
            msg.message_hash(),
            msg.network_num(),
            msg.source_id(),
            msg.short_id(),
            msg.tx_val(),
            transaction_flag,
            msg.timestamp()
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
