from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.v3.broadcast_message_converter_v3 import broadcast_message_converter_v3
from bxcommon.messages.versioning.abstract_version_converter_factory import AbstractMessageConverterFactory
from bxcommon.messages.versioning.no_changes_message_converter import no_changes_message_converter


class _MessageConverterFactoryV3(AbstractMessageConverterFactory):
    _MESSAGE_CONVERTER_MAPPING = {
        BloxrouteMessageType.HELLO: no_changes_message_converter,
        BloxrouteMessageType.TRANSACTION: no_changes_message_converter,
        BloxrouteMessageType.BROADCAST: broadcast_message_converter_v3,
        BloxrouteMessageType.KEY: no_changes_message_converter,

        BloxrouteMessageType.ACK: no_changes_message_converter,
        BloxrouteMessageType.GET_TRANSACTIONS: no_changes_message_converter,
        BloxrouteMessageType.TRANSACTIONS: no_changes_message_converter,
        BloxrouteMessageType.PING: no_changes_message_converter,
        BloxrouteMessageType.PONG: no_changes_message_converter
    }

    def get_message_converter(self, msg_type):
        if not msg_type:
            raise ValueError("msg_type is required.")

        if msg_type not in self._MESSAGE_CONVERTER_MAPPING:
            raise ValueError("Converter for message type '{}' is not defined.".format(msg_type))

        return self._MESSAGE_CONVERTER_MAPPING[msg_type]


message_converter_factory_v3 = _MessageConverterFactoryV3()