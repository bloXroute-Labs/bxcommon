import struct

from bxcommon.constants import NETWORK_NUM_LEN, HDR_COMMON_OFF, DEFAULT_NETWORK_NUM
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.key_message import KeyMessage
from bxcommon.messages.bloxroute.message import Message
from bxcommon.messages.bloxroute.v1.key_message_v1 import KeyMessageV1
from bxcommon.messages.bloxroute.versioning.abstract_message_converter import AbstractMessageConverter
from bxcommon.utils.crypto import KEY_SIZE, SHA256_HASH_LEN


class _KeyMessageConverterV1(AbstractMessageConverter):
    def convert_to_older_version(self, msg):

        if not isinstance(msg, KeyMessage):
            raise TypeError("KeyMessage is expected")

        msg_bytes = msg.rawbytes()
        mem_view = memoryview(msg_bytes)

        result_bytes = bytearray(len(msg_bytes) - NETWORK_NUM_LEN)
        payload_len = len(result_bytes) - HDR_COMMON_OFF

        off = 0
        struct.pack_into("<12sL", result_bytes, off, BloxrouteMessageType.KEY, payload_len)
        off += HDR_COMMON_OFF

        result_bytes[off:off + SHA256_HASH_LEN + KEY_SIZE] = mem_view[off:off + SHA256_HASH_LEN + KEY_SIZE]
        off += KEY_SIZE + SHA256_HASH_LEN

        network_num, = struct.unpack_from("<L", mem_view, off)

        if network_num != DEFAULT_NETWORK_NUM:
            raise ValueError("Key message can be converted to V1 only for default version {}, but was version"
                             .format(DEFAULT_NETWORK_NUM, network_num))

        return Message.initialize_class(KeyMessageV1, result_bytes, (BloxrouteMessageType.KEY, payload_len))

    def convert_from_older_version(self, msg):

        if not isinstance(msg, KeyMessageV1):
            raise TypeError("KeyMessageV1 is expected")

        msg_bytes = msg.rawbytes()
        mem_view = memoryview(msg_bytes)

        result_bytes = bytearray(len(msg_bytes) + NETWORK_NUM_LEN)

        payload_len = len(result_bytes) - HDR_COMMON_OFF

        off = 0
        struct.pack_into("<12sL", result_bytes, off, BloxrouteMessageType.KEY, payload_len)
        off += HDR_COMMON_OFF

        result_bytes[off:off + SHA256_HASH_LEN + KEY_SIZE] = mem_view[off:off + SHA256_HASH_LEN + KEY_SIZE]
        off += KEY_SIZE + SHA256_HASH_LEN

        struct.pack_into("<L", result_bytes, off, DEFAULT_NETWORK_NUM)

        return Message.initialize_class(KeyMessage, result_bytes, (BloxrouteMessageType.KEY, payload_len))

    def convert_first_bytes_to_older_version(self, first_msg_bytes):
        raise NotImplementedError()

    def convert_first_bytes_from_older_version(self, first_msg_bytes):
        raise NotImplementedError()

    def get_message_size_change_to_older_version(self):
        raise NotImplementedError()

    def get_message_size_change_from_older_version(self):
        raise NotImplementedError()


key_message_converter_v1 = _KeyMessageConverterV1()
