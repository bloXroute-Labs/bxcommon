from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.v13.pong_message_converter_v13 import pong_message_converter_v13
from bxcommon.messages.bloxroute.v6.tx_message_converter_v6 import tx_message_converter_v6
from bxcommon.messages.bloxroute.v6.tx_sync_message_converter_v6 import tx_sync_message_converter_v6
from bxcommon.messages.versioning.abstract_version_converter_factory import AbstractMessageConverterFactory
from bxcommon.messages.versioning.no_changes_message_converter import no_changes_message_converter


class _MessageConverterFactoryV6(AbstractMessageConverterFactory):
    _MESSAGE_CONVERTER_MAPPING = {
        BloxrouteMessageType.TRANSACTION: tx_message_converter_v6,
        BloxrouteMessageType.TX_SERVICE_SYNC_TXS: tx_sync_message_converter_v6,
        BloxrouteMessageType.PONG: pong_message_converter_v13
    }

    def get_message_converter(self, msg_type):
        if not msg_type:
            raise ValueError("msg_type is required.")

        if msg_type not in self._MESSAGE_CONVERTER_MAPPING:
            return no_changes_message_converter

        return self._MESSAGE_CONVERTER_MAPPING[msg_type]


message_converter_factory_v6 = _MessageConverterFactoryV6()
