import struct

from bxcommon import constants
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.messages.bloxroute.bloxroute_message_control_flags import BloxrouteMessageControlFlags
from bxcommon.messages.bloxroute.v4.common_message_converter_v4 import _CommonMessageConverterV4
from bxcommon.messages.bloxroute.v4.message_v4 import MessageV4


class _BroadcastMessageConverterV4(_CommonMessageConverterV4):

    def convert_first_bytes_to_older_version(self, msg_first_bytes: memoryview) -> memoryview:
        if len(msg_first_bytes) < AbstractBloxrouteMessage.HEADER_LENGTH:
            raise ValueError("Not enough bytes to convert.")

        command, payload_len = AbstractBloxrouteMessage.unpack(msg_first_bytes)
        result_bytes = bytearray(len(msg_first_bytes) - constants.STARTING_SEQUENCE_BYTES_LEN)

        result_bytes[:] = msg_first_bytes[constants.STARTING_SEQUENCE_BYTES_LEN:]

        struct.pack_into("<12sL", result_bytes, 0, command, payload_len - constants.CONTROL_FLAGS_LEN)

        return memoryview(result_bytes)

    def convert_first_bytes_from_older_version(self, msg_first_bytes: memoryview) -> memoryview:
        if len(msg_first_bytes) < AbstractBloxrouteMessage.HEADER_LENGTH:
            raise ValueError("Not enough bytes to convert.")

        command, payload_len = MessageV4.unpack(msg_first_bytes)
        result_bytes = bytearray(len(msg_first_bytes) + constants.STARTING_SEQUENCE_BYTES_LEN)

        result_bytes[:constants.STARTING_SEQUENCE_BYTES_LEN] = constants.STARTING_SEQUENCE_BYTES
        result_bytes[constants.STARTING_SEQUENCE_BYTES_LEN:] = msg_first_bytes

        struct.pack_into("<12sL", result_bytes, constants.STARTING_SEQUENCE_BYTES_LEN, command, payload_len + constants.CONTROL_FLAGS_LEN)

        return memoryview(result_bytes)

    def convert_last_bytes_to_older_version(self, msg_last_bytes: memoryview) -> memoryview:

        result_bytes = bytearray(len(msg_last_bytes) - constants.CONTROL_FLAGS_LEN)
        result_bytes[:] = msg_last_bytes[:-constants.CONTROL_FLAGS_LEN]

        return memoryview(result_bytes)

    def convert_last_bytes_from_older_version(self, msg_last_bytes: memoryview) -> memoryview:
        result_bytes = bytearray(len(msg_last_bytes) + constants.CONTROL_FLAGS_LEN)
        result_bytes[:-constants.CONTROL_FLAGS_LEN] = msg_last_bytes
        result_bytes[-constants.CONTROL_FLAGS_LEN:] = [BloxrouteMessageControlFlags.VALID]

        return memoryview(result_bytes)

    def get_message_size_change_to_older_version(self) -> int:
        return -(constants.STARTING_SEQUENCE_BYTES_LEN + constants.CONTROL_FLAGS_LEN)

    def get_message_size_change_from_older_version(self) -> int:
        return constants.STARTING_SEQUENCE_BYTES_LEN + constants.CONTROL_FLAGS_LEN


broadcast_message_converter_v4 = _BroadcastMessageConverterV4()
