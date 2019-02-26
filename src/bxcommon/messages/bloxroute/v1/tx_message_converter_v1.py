import struct

from bxcommon.constants import NETWORK_NUM_LEN, HDR_COMMON_OFF, DEFAULT_NETWORK_NUM, UL_INT_SIZE_IN_BYTES
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.message import Message
from bxcommon.messages.bloxroute.tx_message import TxMessage
from bxcommon.messages.bloxroute.v1.tx_message_v1 import TxMessageV1
from bxcommon.messages.versioning.abstract_message_converter import AbstractMessageConverter
from bxcommon.utils.crypto import SHA256_HASH_LEN


class _TxMessageConverterV1(AbstractMessageConverter):
    def convert_to_older_version(self, msg):

        if not isinstance(msg, TxMessage):
            raise TypeError("TxMessage is expected")

        msg_bytes = msg.rawbytes()
        mem_view = memoryview(msg_bytes)

        result_bytes = bytearray(len(msg_bytes) - NETWORK_NUM_LEN)
        payload_len = len(result_bytes) - HDR_COMMON_OFF

        off = 0
        struct.pack_into("<12sL", result_bytes, off, BloxrouteMessageType.TRANSACTION, payload_len)
        off += HDR_COMMON_OFF

        result_bytes[off:off + SHA256_HASH_LEN] = mem_view[off:off + SHA256_HASH_LEN]
        off += SHA256_HASH_LEN

        off_v1 = off

        network_num, = struct.unpack_from("<L", mem_view, off)

        if network_num != DEFAULT_NETWORK_NUM:
            raise ValueError("Tx message can be converted to V1 only for default version {}, but was version"
                             .format(DEFAULT_NETWORK_NUM, network_num))

        off += NETWORK_NUM_LEN

        result_bytes[off_v1:] = mem_view[off:]

        return Message.initialize_class(TxMessageV1, result_bytes, (BloxrouteMessageType.TRANSACTION, payload_len))

    def convert_from_older_version(self, msg):

        if not isinstance(msg, TxMessageV1):
            raise TypeError("TxMessageV1 is expected")

        msg_bytes = msg.rawbytes()
        mem_view = memoryview(msg_bytes)

        result_bytes = bytearray(len(msg_bytes) + NETWORK_NUM_LEN)

        payload_len = len(result_bytes) - HDR_COMMON_OFF

        off = 0
        struct.pack_into("<12sL", result_bytes, off, BloxrouteMessageType.TRANSACTION, payload_len)
        off += HDR_COMMON_OFF

        result_bytes[off:off + SHA256_HASH_LEN] = mem_view[off:off + SHA256_HASH_LEN]
        off += SHA256_HASH_LEN

        off_v1 = off

        struct.pack_into("<L", result_bytes, off, DEFAULT_NETWORK_NUM)
        off += NETWORK_NUM_LEN
        result_bytes[off:] = mem_view[off_v1:]

        return Message.initialize_class(TxMessage, result_bytes, (BloxrouteMessageType.TRANSACTION, payload_len))

    def convert_first_bytes_to_older_version(self, first_msg_bytes):
        raise NotImplementedError()

    def convert_first_bytes_from_older_version(self, first_msg_bytes):
        raise NotImplementedError()

    def get_message_size_change_to_older_version(self):
        raise NotImplementedError()

    def get_message_size_change_from_older_version(self):
        raise NotImplementedError()


tx_message_converter_v1 = _TxMessageConverterV1()
