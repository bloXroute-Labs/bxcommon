from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.v6.tx_message_converter_v6 import tx_message_converter_v6
from bxcommon.messages.bloxroute.v6.tx_sync_message_converter_v6 import tx_sync_message_converter_v6
from bxcommon.messages.versioning.abstract_version_converter_factory import AbstractMessageConverterFactory


class _MessageConverterFactoryV6(AbstractMessageConverterFactory):
    _MESSAGE_CONVERTER_MAPPING = {
        BloxrouteMessageType.TRANSACTION: tx_message_converter_v6,
        BloxrouteMessageType.TX_SERVICE_SYNC_TXS: tx_sync_message_converter_v6
    }

    def get_message_converter(self, msg_type):
        if not msg_type:
            raise ValueError("msg_type is required.")

        if msg_type not in self._MESSAGE_CONVERTER_MAPPING:
            raise ValueError("Converter for message type '{}' is not defined.".format(msg_type))

        return self._MESSAGE_CONVERTER_MAPPING[msg_type]


message_converter_factory_v6 = _MessageConverterFactoryV6()
