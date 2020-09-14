from bxcommon import constants
from bxcommon.messages.abstract_internal_message import AbstractInternalMessage
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.v13.pong_message_v13 import PongMessageV13
from bxcommon.messages.bloxroute.pong_message import PongMessage
from bxcommon.messages.versioning.abstract_message_converter import AbstractMessageConverter


class _PongMessageConverterV13(AbstractMessageConverter):
    _MSG_TYPE_TO_OLD_MSG_CLASS_MAPPING = {
        BloxrouteMessageType.PONG: PongMessageV13
    }

    _MSG_TYPE_TO_NEW_MSG_CLASS_MAPPING = {
        BloxrouteMessageType.PONG: PongMessage
    }

    _BASE_LENGTH = (
        AbstractBloxrouteMessage.HEADER_LENGTH
    )

    _BREAKPOINT = (
        _BASE_LENGTH + constants.UL_ULL_SIZE_IN_BYTES
    )

    _OLD_MESSAGE_LEN = (
        _BASE_LENGTH + PongMessageV13.KEEP_ALIVE_MESSAGE_LENGTH
    )

    _NEW_MESSAGE_LEN = (
        _BASE_LENGTH + PongMessage.PONG_MESSAGE_LENGTH
    )

    _LENGTH_DIFFERENCE = (
        constants.UL_ULL_SIZE_IN_BYTES
    )

    def convert_to_older_version(
        self, msg: AbstractInternalMessage
    ) -> AbstractInternalMessage:
        msg_type = msg.MESSAGE_TYPE

        if msg_type not in self._MSG_TYPE_TO_OLD_MSG_CLASS_MAPPING:
            raise ValueError(
                f"Tried to convert unexpected new message type to v10: {msg_type}"
            )

        old_version_msg_class = self._MSG_TYPE_TO_OLD_MSG_CLASS_MAPPING[
            msg_type
        ]
        old_version_payload_len = msg.payload_len() - self._LENGTH_DIFFERENCE

        old_version_msg_bytes = bytearray(self._OLD_MESSAGE_LEN)
        old_version_msg_bytes[:self._BREAKPOINT] = msg.rawbytes()[:self._BREAKPOINT]
        old_version_msg_bytes[self._BREAKPOINT:] = msg.rawbytes()[self._BREAKPOINT + self._LENGTH_DIFFERENCE:]

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
                f"Tried to convert unexpected old message type from v10: {msg_type}"
            )

        new_msg_class = self._MSG_TYPE_TO_NEW_MSG_CLASS_MAPPING[msg_type]
        new_payload_len = msg.payload_len() + self._LENGTH_DIFFERENCE

        new_msg_bytes = bytearray(self._NEW_MESSAGE_LEN)

        new_msg_bytes[:self._BREAKPOINT] = msg.rawbytes()[:self._BREAKPOINT]

        new_msg_bytes[self._BREAKPOINT + self._LENGTH_DIFFERENCE:] = msg.rawbytes()[self._BREAKPOINT:]

        return AbstractBloxrouteMessage.initialize_class(
            new_msg_class,
            new_msg_bytes,
            (msg_type, new_payload_len)
        )

    def convert_first_bytes_to_older_version(
        self, first_msg_bytes: memoryview
    ) -> memoryview:
        raise NotImplementedError

    def convert_first_bytes_from_older_version(
        self, first_msg_bytes: memoryview
    ) -> memoryview:
        raise NotImplementedError

    def convert_last_bytes_to_older_version(
        self, last_msg_bytes: memoryview
    ) -> memoryview:
        raise NotImplementedError

    def convert_last_bytes_from_older_version(
        self, last_msg_bytes: memoryview
    ) -> memoryview:
        raise NotImplementedError

    def get_message_size_change_to_older_version(self) -> int:
        return -self._LENGTH_DIFFERENCE

    def get_message_size_change_from_older_version(self) -> int:
        return self._LENGTH_DIFFERENCE


pong_message_converter_v13 = _PongMessageConverterV13()
