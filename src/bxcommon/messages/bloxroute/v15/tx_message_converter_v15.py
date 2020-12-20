from typing import cast

from bxcommon.messages.abstract_internal_message import AbstractInternalMessage
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.tx_message import TxMessage
from bxcommon.messages.bloxroute.v15.tx_message_v15 import TxMessageV15
from bxcommon.messages.versioning.abstract_message_converter import AbstractMessageConverter
from bxcommon.models.quota_type_model import QuotaType
from bxcommon.models.transaction_flag import TransactionFlag

from bxutils import logging

logger = logging.get_logger(__name__)


class _TxMessageConverterV15(AbstractMessageConverter):
    _MSG_TYPE_TO_OLD_MSG_CLASS_MAPPING = {
        BloxrouteMessageType.TRANSACTION: TxMessageV15
    }

    _MSG_TYPE_TO_NEW_MSG_CLASS_MAPPING = {
        BloxrouteMessageType.TRANSACTION: TxMessage
    }

    def convert_to_older_version(
        self, msg: AbstractInternalMessage
    ) -> AbstractInternalMessage:
        msg_type = msg.MESSAGE_TYPE

        if msg_type not in self._MSG_TYPE_TO_OLD_MSG_CLASS_MAPPING:
            raise ValueError(
                f"Tried to convert unexpected new "
                f"message type to v15: {msg_type}"
            )

        msg = cast(TxMessage, msg)

        tx_hash = msg.tx_hash()
        network_num = msg.network_num()
        source_id = msg.source_id()
        short_id = msg.short_id()
        tx_val = msg.tx_val()
        quota_type = msg.quota_type()
        ts = msg.timestamp()

        return TxMessageV15(
            message_hash=tx_hash,
            network_num=network_num,
            source_id=source_id,
            short_id=short_id,
            tx_val=tx_val,
            quota_type=quota_type,
            timestamp=ts
        )

    def convert_from_older_version(
        self, msg: AbstractInternalMessage
    ) -> AbstractInternalMessage:
        msg_type = msg.MESSAGE_TYPE

        if msg_type not in self._MSG_TYPE_TO_NEW_MSG_CLASS_MAPPING:
            raise ValueError(
                f"Tried to convert unexpected old message type to "
                f"v15: {msg_type}"
            )

        msg = cast(TxMessageV15, msg)

        tx_hash = msg.tx_hash()
        network_num = msg.network_num()
        source_id = msg.source_id()
        short_id = msg.short_id()
        tx_val = msg.tx_val()
        quota_type = msg.quota_type()
        ts = msg.timestamp()

        if QuotaType.FREE_DAILY_QUOTA in quota_type:
            tx_flag = TransactionFlag.NO_FLAGS
        else:
            tx_flag = TransactionFlag.PAID_TX

        return TxMessage(
            message_hash=tx_hash,
            network_num=network_num,
            source_id=source_id,
            short_id=short_id,
            tx_val=tx_val,
            transaction_flag=tx_flag,
            timestamp=ts
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
        raise NotImplementedError

    def get_message_size_change_from_older_version(self) -> int:
        raise NotImplementedError


tx_message_converter_v15 = _TxMessageConverterV15()
