import struct

from bxcommon.constants import HDR_COMMON_OFF, UL_INT_SIZE_IN_BYTES
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.message import Message
from bxcommon.messages.bloxroute.version_message import VersionMessage
from bxcommon.messages.versioning.abstract_message_converter import AbstractMessageConverter

from bxcommon.messages.bloxroute.hello_message import HelloMessage
from bxcommon.messages.bloxroute.v2.hello_message_v2 import HelloMessageV2
from bxcommon.utils import uuid_pack


class _HelloMessageConverterV2(AbstractMessageConverter):
    def convert_to_older_version(self, msg):
        if not isinstance(msg, HelloMessage):
            raise TypeError("HelloMessage is expected")

        msg_bytes = msg.rawbytes()
        mem_view = memoryview(msg_bytes)

        result_bytes = bytearray(len(msg_bytes.tobytes()) - HelloMessage.HELLO_MESSAGE_BLOCK.size + UL_INT_SIZE_IN_BYTES)
        payload_len = HelloMessageV2.HelloMessageLength

        result_bytes[:] = mem_view[:HDR_COMMON_OFF + HelloMessageV2.HelloMessageLength]
        struct.pack_into("<L", result_bytes, VersionMessage.BASE_LENGTH, 0)  # fill idx value with 0
        return Message.initialize_class(HelloMessageV2, result_bytes, (BloxrouteMessageType.HELLO, payload_len))

    def convert_from_older_version(self, msg):
        if not isinstance(msg, HelloMessageV2):
            raise TypeError("HelloMessageV2 is expected")

        msg_bytes = msg.rawbytes()
        mem_view = memoryview(msg_bytes)

        result_bytes = bytearray(HDR_COMMON_OFF + HelloMessage.HELLO_MESSAGE_LENGTH)
        payload_len = HelloMessage.HELLO_MESSAGE_LENGTH
        result_bytes[:len(msg.buf)] = msg.buf[:]
        off = len(msg.buf)
        off -= UL_INT_SIZE_IN_BYTES  # remove idx section
        struct.pack_into("%ss" % HelloMessage.HELLO_MESSAGE_BLOCK.size, result_bytes, off, uuid_pack.to_bytes(b""))
        return Message.initialize_class(HelloMessage, result_bytes, (BloxrouteMessageType.HELLO, payload_len))

    def convert_first_bytes_to_older_version(self, first_msg_bytes):
        raise NotImplementedError()

    def convert_first_bytes_from_older_version(self, first_msg_bytes):
        raise NotImplementedError()

    def get_message_size_change_to_older_version(self):
        raise NotImplementedError()

    def get_message_size_change_from_older_version(self):
        raise NotImplementedError()


hello_message_converter_v2 = _HelloMessageConverterV2()

