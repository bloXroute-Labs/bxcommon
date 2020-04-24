import struct

from bxcommon import constants
from bxcommon.messages.abstract_internal_message import AbstractInternalMessage
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.messages.bloxroute.abstract_broadcast_message import AbstractBroadcastMessage
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.broadcast_message import BroadcastMessage
from bxcommon.messages.bloxroute.v8.broadcast_message_v8 import BroadcastMessageV8
from bxcommon.messages.versioning.abstract_message_converter import AbstractMessageConverter
from bxcommon.models.broadcast_message_type import BroadcastMessageType


class _BroadcastMessageConverterV8(AbstractMessageConverter):
    _MSG_TYPE_TO_OLD_MSG_CLASS_MAPPING = {
        BloxrouteMessageType.BROADCAST: BroadcastMessageV8
    }

    _MSG_TYPE_TO_NEW_MSG_CLASS_MAPPING = {
        BloxrouteMessageType.BROADCAST: BroadcastMessage
    }

    _BASE_LENGTH = (
        AbstractBroadcastMessage.HEADER_LENGTH
        + AbstractBroadcastMessage.PAYLOAD_LENGTH
        - constants.CONTROL_FLAGS_LEN
    )

    _BREAKPOINT = (
        _BASE_LENGTH + constants.BROADCAST_TYPE_LEN
    )

    def convert_to_older_version(
        self, msg: AbstractInternalMessage
    ) -> AbstractInternalMessage:
        msg_type = msg.MESSAGE_TYPE

        if msg_type not in self._MSG_TYPE_TO_OLD_MSG_CLASS_MAPPING:
            raise ValueError(
                f"Tried to convert unexpected new message type to v8: {msg_type}"
            )

        old_version_msg_class = self._MSG_TYPE_TO_OLD_MSG_CLASS_MAPPING[
            msg_type
        ]
        old_version_payload_len = msg.payload_len() - constants.BROADCAST_TYPE_LEN

        old_version_msg_bytes = bytearray(self._BASE_LENGTH + len(msg.rawbytes()[self._BREAKPOINT:]))
        old_version_msg_bytes[:self._BASE_LENGTH] = msg.rawbytes()[:self._BASE_LENGTH]
        old_version_msg_bytes[self._BASE_LENGTH:] = msg.rawbytes()[self._BREAKPOINT:]

        return AbstractBloxrouteMessage.initialize_class(
            old_version_msg_class,
            old_version_msg_bytes,
            (msg_type, old_version_payload_len),
        )

    def convert_from_older_version(
        self, msg: AbstractInternalMessage
    ) -> AbstractInternalMessage:
        msg_type = msg.MESSAGE_TYPE

        if msg_type not in self._MSG_TYPE_TO_NEW_MSG_CLASS_MAPPING:
            raise ValueError(
                f"Tried to convert unexpected old message type to v9: {msg_type}"
            )

        new_msg_class = self._MSG_TYPE_TO_NEW_MSG_CLASS_MAPPING[msg_type]
        new_payload_len = msg.payload_len() + constants.BROADCAST_TYPE_LEN

        new_msg_bytes = bytearray(AbstractBloxrouteMessage.HEADER_LENGTH + new_payload_len)
        new_msg_bytes[:self._BASE_LENGTH] = msg.rawbytes()[:self._BASE_LENGTH]
        struct.pack_into(
            "<4s",
            new_msg_bytes,
            self._BASE_LENGTH,
            # pylint: disable=no-member
            BroadcastMessageType.BLOCK.value.encode(constants.DEFAULT_TEXT_ENCODING)
        )
        new_msg_bytes[self._BREAKPOINT:] = msg.rawbytes()[self._BASE_LENGTH:]

        return AbstractBloxrouteMessage.initialize_class(
            new_msg_class,
            new_msg_bytes,
            (msg_type, new_payload_len)
        )

    def convert_first_bytes_to_older_version(
        self, first_msg_bytes: memoryview
    ) -> memoryview:
        if len(first_msg_bytes) < AbstractBloxrouteMessage.HEADER_LENGTH + AbstractBroadcastMessage.PAYLOAD_LENGTH - \
                constants.CONTROL_FLAGS_LEN:
            raise ValueError("Not enough bytes to convert.")
        command, payload_len = BroadcastMessage.unpack(first_msg_bytes)

        result_bytes = bytearray(len(first_msg_bytes) - constants.BROADCAST_TYPE_LEN)

        result_bytes[:self._BASE_LENGTH] = first_msg_bytes[:self._BASE_LENGTH]
        result_bytes[self._BASE_LENGTH:] = first_msg_bytes[self._BREAKPOINT:]

        struct.pack_into("<12sL", result_bytes, constants.STARTING_SEQUENCE_BYTES_LEN, command,
                         payload_len - constants.BROADCAST_TYPE_LEN)

        return memoryview(result_bytes)

    def convert_first_bytes_from_older_version(
        self, first_msg_bytes: memoryview
    ) -> memoryview:
        if len(first_msg_bytes) < AbstractBloxrouteMessage.HEADER_LENGTH + AbstractBroadcastMessage.PAYLOAD_LENGTH - \
                constants.CONTROL_FLAGS_LEN:
            raise ValueError("Not enough bytes to convert.")
        command, payload_len = BroadcastMessageV8.unpack(first_msg_bytes)

        result_bytes = bytearray(len(first_msg_bytes) + constants.BROADCAST_TYPE_LEN)

        result_bytes[:self._BASE_LENGTH] = first_msg_bytes[:self._BASE_LENGTH]
        result_bytes[self._BREAKPOINT:] = first_msg_bytes[self._BASE_LENGTH:]
        struct.pack_into(
            "<4s",
            result_bytes,
            self._BASE_LENGTH,
            # pylint: disable=no-member
            BroadcastMessageType.BLOCK.value.encode(constants.DEFAULT_TEXT_ENCODING)
        )

        struct.pack_into("<12sL", result_bytes, constants.STARTING_SEQUENCE_BYTES_LEN, command,
                         payload_len + constants.BROADCAST_TYPE_LEN)

        return memoryview(result_bytes)

    def convert_last_bytes_to_older_version(
        self, last_msg_bytes: memoryview
    ) -> memoryview:
        return last_msg_bytes

    def convert_last_bytes_from_older_version(
        self, last_msg_bytes: memoryview
    ) -> memoryview:
        return last_msg_bytes

    def get_message_size_change_to_older_version(self) -> int:
        return -constants.BROADCAST_TYPE_LEN

    def get_message_size_change_from_older_version(self) -> int:
        return constants.BROADCAST_TYPE_LEN


broadcast_message_converter_v8 = _BroadcastMessageConverterV8()
