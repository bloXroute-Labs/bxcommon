from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.v1.key_message_converter_v1 import key_message_converter_v1
from bxcommon.messages.bloxroute.v1.tx_message_converter_v1 import tx_message_converter_v1
from bxcommon.messages.bloxroute.v1.broadcast_message_converter_v1 import broadcast_message_converter_v1
from bxcommon.messages.bloxroute.v2.hello_message_converter_v2 import hello_message_converter_v2
from bxcommon.messages.bloxroute.v1.keep_alive_message_converter_v1 import ping_message_converter_v1,\
    pong_message_converter_v1
from bxcommon.messages.versioning.abstract_version_converter_factory import AbstractMessageConverterFactory
from bxcommon.messages.versioning.no_changes_message_converter import no_changes_message_converter


class _MessageConverterFactoryV2(AbstractMessageConverterFactory):

    _MESSAGE_CONVERTER_MAPPING = {
        BloxrouteMessageType.HELLO: hello_message_converter_v2,
        BloxrouteMessageType.TRANSACTION: no_changes_message_converter,
        BloxrouteMessageType.BROADCAST: no_changes_message_converter,
        BloxrouteMessageType.KEY: no_changes_message_converter,

        BloxrouteMessageType.ACK: no_changes_message_converter,
        BloxrouteMessageType.GET_TRANSACTIONS: no_changes_message_converter,
        BloxrouteMessageType.TRANSACTIONS: no_changes_message_converter,
        BloxrouteMessageType.PING: ping_message_converter_v1,
        BloxrouteMessageType.PONG: pong_message_converter_v1
    }

    def get_message_converter(self, msg_type):
        if not msg_type:
            raise ValueError("msg_type is required.")

        if msg_type not in self._MESSAGE_CONVERTER_MAPPING:
            raise ValueError("Converter for message type '{}' is not defined.".format(msg_type))

        return self._MESSAGE_CONVERTER_MAPPING[msg_type]


message_converter_factory_v2 = _MessageConverterFactoryV2()
