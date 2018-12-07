import struct

from bxcommon.constants import NETWORK_NUM_LEN, HDR_COMMON_OFF, DEFAULT_NETWORK_NUM
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.broadcast_message import BroadcastMessage
from bxcommon.messages.bloxroute.message import Message
from bxcommon.messages.bloxroute.v1.broadcast_message_v1 import BroadcastMessageV1
from bxcommon.messages.versioning.abstract_message_converter import AbstractMessageConverter
from bxcommon.utils.crypto import SHA256_HASH_LEN


class _BroadcastMessageConverterV1(AbstractMessageConverter):
    def convert_to_older_version(self, msg):

        if not isinstance(msg, BroadcastMessage):
            raise TypeError("BroadcastMessage is expected")

        msg_bytes = msg.rawbytes()
        mem_view = memoryview(msg_bytes)

        result_bytes = bytearray(len(msg_bytes) - NETWORK_NUM_LEN)
        payload_len = len(result_bytes) - HDR_COMMON_OFF

        off_v1 = 0
        struct.pack_into("<12sL", result_bytes, off_v1, BloxrouteMessageType.BROADCAST, payload_len)
        off_v1 += HDR_COMMON_OFF
        off = off_v1

        result_bytes[off_v1:off_v1 + SHA256_HASH_LEN] = mem_view[off:off + SHA256_HASH_LEN]
        off_v1 += SHA256_HASH_LEN
        off += SHA256_HASH_LEN + NETWORK_NUM_LEN

        result_bytes[off_v1:] = mem_view[off:]

        return Message.initialize_class(BroadcastMessageV1, result_bytes, (BloxrouteMessageType.BROADCAST, payload_len))

    def convert_from_older_version(self, msg):

        if not isinstance(msg, BroadcastMessageV1):
            raise TypeError("BroadcastMessageV1 is expected")

        msg_bytes = msg.rawbytes()
        mem_view = memoryview(msg_bytes)

        result_bytes = bytearray(len(msg_bytes) + NETWORK_NUM_LEN)
        payload_len = len(result_bytes) - HDR_COMMON_OFF

        off = 0
        struct.pack_into("<12sL", result_bytes, off, BloxrouteMessageType.BROADCAST, payload_len)
        off += HDR_COMMON_OFF
        off_v1 = off

        result_bytes[off_v1:off_v1 + SHA256_HASH_LEN] = mem_view[off:off + SHA256_HASH_LEN]
        off_v1 += SHA256_HASH_LEN
        off += SHA256_HASH_LEN

        struct.pack_into("<L", result_bytes, off, DEFAULT_NETWORK_NUM)
        off += NETWORK_NUM_LEN

        result_bytes[off:] = mem_view[off_v1:]

        return Message.initialize_class(BroadcastMessage, result_bytes, (BloxrouteMessageType.BROADCAST, payload_len))

    def convert_first_bytes_to_older_version(self, first_msg_bytes):
        if len(first_msg_bytes) < HDR_COMMON_OFF + SHA256_HASH_LEN + NETWORK_NUM_LEN:
            raise ValueError("Not enough bytes to convert.")

        unpacked_args = Message.unpack(first_msg_bytes)

        # updating payload length
        payload_len = unpacked_args[1] - NETWORK_NUM_LEN

        result_bytes = bytearray(len(first_msg_bytes) - NETWORK_NUM_LEN)

        off_v1 = 0
        struct.pack_into("<12sL", result_bytes, off_v1, unpacked_args[0], payload_len)
        off_v1 += HDR_COMMON_OFF
        off = off_v1

        result_bytes[off_v1:off_v1 + SHA256_HASH_LEN] = first_msg_bytes[off:off + SHA256_HASH_LEN]
        off += SHA256_HASH_LEN + NETWORK_NUM_LEN
        off_v1 += SHA256_HASH_LEN

        result_bytes[off_v1:] = first_msg_bytes[off:]

        return result_bytes

    def convert_first_bytes_from_older_version(self, first_msg_bytes):
        if len(first_msg_bytes) < HDR_COMMON_OFF + SHA256_HASH_LEN + NETWORK_NUM_LEN:
            raise ValueError("Not enough bytes to convert.")

        unpacked_args = Message.unpack(first_msg_bytes)

        # updating payload length
        payload_len = unpacked_args[1] + NETWORK_NUM_LEN

        result_bytes = bytearray(len(first_msg_bytes) + NETWORK_NUM_LEN)

        off = 0
        struct.pack_into("<12sL", result_bytes, off, unpacked_args[0], payload_len)
        off += HDR_COMMON_OFF
        off_v1 = off

        result_bytes[off:off + SHA256_HASH_LEN] = first_msg_bytes[off_v1:off_v1 + SHA256_HASH_LEN]
        off += SHA256_HASH_LEN
        off_v1 += SHA256_HASH_LEN

        struct.pack_into("<L", result_bytes, off, DEFAULT_NETWORK_NUM)
        off += NETWORK_NUM_LEN

        result_bytes[off:] = first_msg_bytes[off_v1:]

        return result_bytes

    def get_message_size_change_to_older_version(self):
        return -NETWORK_NUM_LEN

    def get_message_size_change_from_older_version(self):
        return NETWORK_NUM_LEN

broadcast_message_converter_v1 = _BroadcastMessageConverterV1()