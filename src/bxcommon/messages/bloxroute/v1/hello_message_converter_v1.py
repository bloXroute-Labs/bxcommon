import struct

from bxcommon.constants import NETWORK_NUM_LEN, HDR_COMMON_OFF, DEFAULT_NETWORK_NUM, VERSION_NUM_LEN, \
    UL_INT_SIZE_IN_BYTES
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.hello_message import HelloMessage
from bxcommon.messages.bloxroute.message import Message
from bxcommon.messages.bloxroute.v1.hello_message_v1 import HelloMessageV1
from bxcommon.messages.bloxroute.versioning.abstract_message_converter import AbstractMessageConverter


class _HelloMessageConverterV1(AbstractMessageConverter):
    def convert_to_older_version(self, msg):

        if not isinstance(msg, HelloMessage):
            raise TypeError("BroadcastMessage is expected")

        msg_bytes = msg.rawbytes()
        mem_view = memoryview(msg_bytes)

        result_bytes = bytearray(len(msg_bytes) - NETWORK_NUM_LEN - VERSION_NUM_LEN)
        payload_len = len(result_bytes) - HDR_COMMON_OFF

        off_v1 = 0
        struct.pack_into("<12sL", result_bytes, off_v1, BloxrouteMessageType.HELLO, payload_len)
        off_v1 += HDR_COMMON_OFF

        off = off_v1 + NETWORK_NUM_LEN
        result_bytes[off_v1:] = mem_view[off:]

        return Message.initialize_class(HelloMessageV1, result_bytes, (BloxrouteMessageType.HELLO, payload_len))

    def convert_from_older_version(self, msg):

        if not isinstance(msg, HelloMessageV1):
            raise TypeError("BroadcastMessageV1 is expected")

        msg_bytes = msg.rawbytes()
        mem_view = memoryview(msg_bytes)

        result_bytes = bytearray(len(msg_bytes) + NETWORK_NUM_LEN + VERSION_NUM_LEN)
        payload_len = len(result_bytes) - HDR_COMMON_OFF

        off_v1 = 0

        struct.pack_into("<12sL", result_bytes, off_v1, BloxrouteMessageType.HELLO, payload_len)
        off_v1 += HDR_COMMON_OFF
        off = off_v1

        # Add default version
        struct.pack_into("<L", result_bytes, off, 1)
        off += VERSION_NUM_LEN

        # copy IDx
        result_bytes[off:off + UL_INT_SIZE_IN_BYTES] = mem_view[off_v1:off_v1 + UL_INT_SIZE_IN_BYTES]
        off += UL_INT_SIZE_IN_BYTES

        # pack default network number
        struct.pack_into("<L", result_bytes, off, DEFAULT_NETWORK_NUM)

        return Message.initialize_class(HelloMessage, result_bytes, (BloxrouteMessageType.HELLO, payload_len))

    def convert_first_bytes_to_older_version(self, first_msg_bytes):
        raise NotImplementedError()

    def convert_first_bytes_from_older_version(self, first_msg_bytes):
        raise NotImplementedError()

    def get_message_size_change_to_older_version(self):
        raise NotImplementedError()

    def get_message_size_change_from_older_version(self):
        raise NotImplementedError()


hello_message_converter_v1 = _HelloMessageConverterV1()
