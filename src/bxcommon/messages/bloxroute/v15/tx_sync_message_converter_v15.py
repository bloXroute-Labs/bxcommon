from typing import cast

from bxcommon.messages.abstract_internal_message import AbstractInternalMessage
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.tx_service_sync_txs_message import TxServiceSyncTxsMessage
from bxcommon.messages.bloxroute.txs_serializer import TxContentShortIds
from bxcommon.messages.bloxroute.v15.tx_service_sync_txs_message_v15 import TxServiceSyncTxsMessageV15, \
    TxContentShortIdsV15
from bxcommon.messages.versioning.abstract_message_converter import AbstractMessageConverter
from bxcommon.models.transaction_flag import TransactionFlag


class _TxSyncMessageConverterV15(AbstractMessageConverter):
    _MSG_TYPE_TO_OLD_MSG_CLASS_MAPPING = {
        BloxrouteMessageType.TX_SERVICE_SYNC_TXS: TxServiceSyncTxsMessageV15
    }

    _MSG_TYPE_TO_NEW_MSG_CLASS_MAPPING = {
        BloxrouteMessageType.TX_SERVICE_SYNC_TXS: TxServiceSyncTxsMessage
    }

    def convert_to_older_version(self, msg: AbstractInternalMessage) -> AbstractInternalMessage:
        msg_type = msg.MESSAGE_TYPE
        if msg_type not in self._MSG_TYPE_TO_OLD_MSG_CLASS_MAPPING:
            raise ValueError(f"Tried to convert unexpected new message type to v15: {msg_type}")
        msg = cast(TxServiceSyncTxsMessage, msg)

        txs_content_short_ids = msg.txs_content_short_ids()
        txs_content_short_ids_v15 = [
            TxContentShortIdsV15(
                item.tx_hash, item.tx_content, item.short_ids,
                [short_id_flag.get_quota_type() for short_id_flag in item.short_id_flags]
            ) for item in txs_content_short_ids
        ]
        network_num = msg.network_num()

        return TxServiceSyncTxsMessageV15(network_num, txs_content_short_ids_v15)

    def convert_from_older_version(self, msg: AbstractInternalMessage) -> AbstractInternalMessage:
        msg_type = msg.MESSAGE_TYPE

        if msg_type not in self._MSG_TYPE_TO_NEW_MSG_CLASS_MAPPING:
            raise ValueError(f"Tried to convert unexpected old message type to v15: {msg_type}")
        msg = cast(TxServiceSyncTxsMessageV15, msg)

        txs_content_short_ids_v15 = msg.txs_content_short_ids()
        txs_content_short_ids = [
            TxContentShortIds(
                item.tx_hash,
                item.tx_content,
                item.short_ids,
                [TransactionFlag(short_id_flag.value) for short_id_flag in item.short_id_flags]
                )
            for item in txs_content_short_ids_v15
        ]
        network_num = msg.network_num()

        return TxServiceSyncTxsMessage(network_num, txs_content_short_ids)

    def convert_first_bytes_to_older_version(self, first_msg_bytes: memoryview) -> memoryview:
        raise NotImplementedError

    def convert_first_bytes_from_older_version(self, first_msg_bytes: memoryview) -> memoryview:
        raise NotImplementedError

    def convert_last_bytes_to_older_version(self, last_msg_bytes: memoryview) -> memoryview:
        raise NotImplementedError

    def convert_last_bytes_from_older_version(self, last_msg_bytes: memoryview) -> memoryview:
        raise NotImplementedError

    def get_message_size_change_to_older_version(self) -> int:
        raise NotImplementedError

    def get_message_size_change_from_older_version(self) -> int:
        raise NotImplementedError


tx_sync_message_converter_v15 = _TxSyncMessageConverterV15()
