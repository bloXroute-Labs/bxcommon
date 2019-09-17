import struct

from bxcommon import constants
from bxcommon.messages.abstract_internal_message import AbstractInternalMessage
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.messages.bloxroute.bloxroute_message_control_flags import BloxrouteMessageControlFlags
from bxcommon.messages.bloxroute.v4.common_message_converter_v4 import _CommonMessageConverterV4
from bxcommon.messages.bloxroute.v4.message_v4 import MessageV4
from bxcommon.messages.bloxroute.v5.broadcast_message_converter_v5 import broadcast_message_converter_v5


class _BroadcastMessageConverterV4(_CommonMessageConverterV4):

    def convert_to_older_version(self, msg: AbstractInternalMessage) -> AbstractInternalMessage:
        v5_msg = broadcast_message_converter_v5.convert_to_older_version(msg)
        return super().convert_to_older_version(v5_msg)

    def convert_from_older_version(self, msg: AbstractInternalMessage) -> AbstractInternalMessage:
        v5_msg = super().convert_from_older_version(msg)
        return broadcast_message_converter_v5.convert_from_older_version(v5_msg)

    def convert_first_bytes_to_older_version(self, first_msg_bytes: memoryview) -> memoryview:
        v5_bytes = broadcast_message_converter_v5.convert_first_bytes_to_older_version(first_msg_bytes)

        command, payload_len = AbstractBloxrouteMessage.unpack(v5_bytes)
        result_bytes = bytearray(len(v5_bytes) - constants.STARTING_SEQUENCE_BYTES_LEN)

        result_bytes[:] = v5_bytes[constants.STARTING_SEQUENCE_BYTES_LEN:]

        struct.pack_into("<12sL", result_bytes, 0, command, payload_len - constants.CONTROL_FLAGS_LEN)

        return memoryview(result_bytes)

    def convert_first_bytes_from_older_version(self, first_msg_bytes: memoryview) -> memoryview:
        command, payload_len = MessageV4.unpack(first_msg_bytes)
        result_bytes = bytearray(len(first_msg_bytes) + constants.STARTING_SEQUENCE_BYTES_LEN)

        result_bytes[:constants.STARTING_SEQUENCE_BYTES_LEN] = constants.STARTING_SEQUENCE_BYTES
        result_bytes[constants.STARTING_SEQUENCE_BYTES_LEN:] = first_msg_bytes

        struct.pack_into("<12sL", result_bytes, constants.STARTING_SEQUENCE_BYTES_LEN, command,
                         payload_len + constants.CONTROL_FLAGS_LEN)

        return broadcast_message_converter_v5.convert_first_bytes_from_older_version(memoryview(result_bytes))

    def convert_last_bytes_to_older_version(self, last_msg_bytes: memoryview) -> memoryview:

        result_bytes = bytearray(len(last_msg_bytes) - constants.CONTROL_FLAGS_LEN)
        result_bytes[:] = last_msg_bytes[:-constants.CONTROL_FLAGS_LEN]

        return memoryview(result_bytes)

    def convert_last_bytes_from_older_version(self, last_msg_bytes: memoryview) -> memoryview:
        result_bytes = bytearray(len(last_msg_bytes) + constants.CONTROL_FLAGS_LEN)
        result_bytes[:-constants.CONTROL_FLAGS_LEN] = last_msg_bytes
        result_bytes[-constants.CONTROL_FLAGS_LEN:] = [BloxrouteMessageControlFlags.VALID]

        return memoryview(result_bytes)

    def get_message_size_change_to_older_version(self) -> int:
        return -(constants.STARTING_SEQUENCE_BYTES_LEN + constants.CONTROL_FLAGS_LEN + constants.NODE_ID_SIZE_IN_BYTES)

    def get_message_size_change_from_older_version(self) -> int:
        return constants.STARTING_SEQUENCE_BYTES_LEN + constants.CONTROL_FLAGS_LEN + constants.NODE_ID_SIZE_IN_BYTES


broadcast_message_converter_v4 = _BroadcastMessageConverterV4()
