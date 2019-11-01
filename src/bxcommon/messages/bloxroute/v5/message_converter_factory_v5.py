from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.v5.broadcast_message_converter_v5 import broadcast_message_converter_v5
from bxcommon.messages.versioning.abstract_version_converter_factory import AbstractMessageConverterFactory


class _MessageConverterFactoryV5(AbstractMessageConverterFactory):
    _MESSAGE_CONVERTER_MAPPING = {
        BloxrouteMessageType.BROADCAST: broadcast_message_converter_v5,
        BloxrouteMessageType.TRANSACTION: broadcast_message_converter_v5,
        BloxrouteMessageType.KEY: broadcast_message_converter_v5,
        BloxrouteMessageType.BLOCK_HOLDING: broadcast_message_converter_v5
    }

    def get_message_converter(self, msg_type):
        if not msg_type:
            raise ValueError("msg_type is required.")

        if msg_type not in self._MESSAGE_CONVERTER_MAPPING:
            raise ValueError("Converter for message type '{}' is not defined.".format(msg_type))

        return self._MESSAGE_CONVERTER_MAPPING[msg_type]


message_converter_factory_v5 = _MessageConverterFactoryV5()
