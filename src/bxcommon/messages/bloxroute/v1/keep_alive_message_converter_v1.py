from bxcommon.constants import HDR_COMMON_OFF
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.message import Message
from bxcommon.messages.versioning.abstract_message_converter import AbstractMessageConverter

from bxcommon.messages.bloxroute.v1.keep_alive_message_v1 import KeepAliveMessageV1
from bxcommon.messages.bloxroute.keep_alive_message import KeepAliveMessage
from bxcommon.messages.bloxroute.v1.ping_message_v1 import PingMessageV1
from bxcommon.messages.bloxroute.ping_message import PingMessage
from bxcommon.messages.bloxroute.v1.pong_message_v1 import PongMessageV1
from bxcommon.messages.bloxroute.pong_message import PongMessage


class _KeepAliveMessageConverterV1(AbstractMessageConverter):
    CLASS_TYPE_OLD = KeepAliveMessageV1
    CLASS_TYPE_NEW = KeepAliveMessage
    MSG_TYPE = None

    def convert_to_older_version(self, msg):
        if not isinstance(msg, KeepAliveMessage):
            raise TypeError("KeepAliveMessage is expected")

        msg_bytes = msg.rawbytes()
        mem_view = memoryview(msg_bytes)

        result_bytes = bytearray(HDR_COMMON_OFF)
        payload_len = 0

        result_bytes[:] = mem_view[:HDR_COMMON_OFF + payload_len]
        return Message.initialize_class(self.CLASS_TYPE_OLD, result_bytes, (self.MSG_TYPE, payload_len))

    def convert_from_older_version(self, msg):
        if not isinstance(msg, KeepAliveMessageV1):
            raise TypeError("KeepAliveMessageV1 is expected")

        msg_bytes = msg.rawbytes()
        mem_view = memoryview(msg_bytes)

        result_bytes = bytearray(HDR_COMMON_OFF + KeepAliveMessage.KEEP_ALIVE_MESSAGE_LENGTH)
        payload_len = KeepAliveMessage.KEEP_ALIVE_MESSAGE_LENGTH
        result_bytes[:len(msg.buf)] = msg.buf[:]
        off = len(msg.buf)
        return Message.initialize_class(self.CLASS_TYPE_NEW, result_bytes, (self.MSG_TYPE, payload_len))

    def convert_first_bytes_to_older_version(self, first_msg_bytes):
        raise NotImplementedError()

    def convert_first_bytes_from_older_version(self, first_msg_bytes):
        raise NotImplementedError()

    def get_message_size_change_to_older_version(self):
        raise NotImplementedError()

    def get_message_size_change_from_older_version(self):
        raise NotImplementedError()


class _PingMessageConverterV1(_KeepAliveMessageConverterV1):
    CLASS_TYPE_OLD = PingMessageV1
    CLASS_TYPE_NEW = PingMessage
    MSG_TYPE = BloxrouteMessageType.PING


class _PongMessageConverterV1(_KeepAliveMessageConverterV1):
    CLASS_TYPE_OLD = PongMessageV1
    CLASS_TYPE_NEW = PongMessage
    MSG_TYPE = BloxrouteMessageType.PONG


ping_message_converter_v1 = _PingMessageConverterV1()
pong_message_converter_v1 = _PongMessageConverterV1()

