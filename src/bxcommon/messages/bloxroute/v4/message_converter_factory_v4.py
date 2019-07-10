from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.v4.broadcast_message_converter_v4 import broadcast_message_converter_v4
from bxcommon.messages.bloxroute.v4.common_message_converter_v4 import common_message_converter_v4
from bxcommon.messages.versioning.abstract_version_converter_factory import AbstractMessageConverterFactory


class _MessageConverterFactoryV4(AbstractMessageConverterFactory):
    _MESSAGE_CONVERTER_MAPPING = {
        BloxrouteMessageType.HELLO: common_message_converter_v4,
        BloxrouteMessageType.ACK: common_message_converter_v4,
        BloxrouteMessageType.PING: common_message_converter_v4,
        BloxrouteMessageType.PONG: common_message_converter_v4,
        BloxrouteMessageType.BROADCAST: broadcast_message_converter_v4,
        BloxrouteMessageType.TRANSACTION: common_message_converter_v4,
        BloxrouteMessageType.GET_TRANSACTIONS: common_message_converter_v4,
        BloxrouteMessageType.TRANSACTIONS: common_message_converter_v4,
        BloxrouteMessageType.KEY: common_message_converter_v4,
        BloxrouteMessageType.BLOCK_HOLDING: common_message_converter_v4
    }

    def get_message_converter(self, msg_type):
        if not msg_type:
            raise ValueError("msg_type is required.")

        if msg_type not in self._MESSAGE_CONVERTER_MAPPING:
            raise ValueError("Converter for message type '{}' is not defined.".format(msg_type))

        return self._MESSAGE_CONVERTER_MAPPING[msg_type]


message_converter_factory_v4 = _MessageConverterFactoryV4()
