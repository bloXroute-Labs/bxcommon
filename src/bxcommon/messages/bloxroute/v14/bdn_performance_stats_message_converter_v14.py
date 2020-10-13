import struct

from bxcommon import constants
from bxcommon.messages.abstract_internal_message import AbstractInternalMessage
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.messages.bloxroute.bdn_performance_stats_message import BdnPerformanceStatsMessage
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.v14.bdn_performance_stats_message_v14 import \
    BdnPerformanceStatsMessageV14
from bxcommon.messages.versioning.abstract_message_converter import AbstractMessageConverter


class _BdnPerformanceStatsMessageConverterV14(AbstractMessageConverter):
    _MSG_TYPE_TO_OLD_MSG_CLASS_MAPPING = {
        BloxrouteMessageType.BDN_PERFORMANCE_STATS: BdnPerformanceStatsMessageV14
    }

    _MSG_TYPE_TO_NEW_MSG_CLASS_MAPPING = {
        BloxrouteMessageType.BDN_PERFORMANCE_STATS: BdnPerformanceStatsMessage
    }

    _BASE_LENGTH = (
        AbstractBloxrouteMessage.HEADER_LENGTH
    )

    _BREAKPOINT = (
        AbstractBloxrouteMessage.HEADER_LENGTH +
        2 * constants.DOUBLE_SIZE_IN_BYTES +
        3 * constants.UL_SHORT_SIZE_IN_BYTES +
        2 * constants.UL_INT_SIZE_IN_BYTES
    )

    _OLD_MESSAGE_LEN = BdnPerformanceStatsMessageV14.MSG_SIZE
    _NEW_MESSAGE_LEN = BdnPerformanceStatsMessage.MSG_SIZE
    _LENGTH_DIFFERENCE = _NEW_MESSAGE_LEN - _OLD_MESSAGE_LEN

    def convert_to_older_version(
        self, msg: AbstractInternalMessage
    ) -> AbstractInternalMessage:
        msg_type = msg.MESSAGE_TYPE

        if msg_type not in self._MSG_TYPE_TO_OLD_MSG_CLASS_MAPPING:
            raise ValueError(
                f"Tried to convert unexpected new message type to v14: {msg_type}"
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
                f"Tried to convert unexpected old message type from v14: {msg_type}"
            )

        new_msg_class = self._MSG_TYPE_TO_NEW_MSG_CLASS_MAPPING[msg_type]
        new_payload_len = msg.payload_len() + self._LENGTH_DIFFERENCE

        new_msg_bytes = bytearray(self._NEW_MESSAGE_LEN)
        new_msg_bytes[:self._BREAKPOINT] = msg.rawbytes()[:self._BREAKPOINT]

        default_new_stats = 0
        offset = self._BREAKPOINT
        struct.pack_into("<I", new_msg_bytes, offset, default_new_stats)
        offset += constants.UL_INT_SIZE_IN_BYTES
        struct.pack_into("<I", new_msg_bytes, offset, default_new_stats)
        offset += constants.UL_INT_SIZE_IN_BYTES
        struct.pack_into("<I", new_msg_bytes, offset, default_new_stats)
        offset += constants.UL_INT_SIZE_IN_BYTES

        new_msg_bytes[offset:] = msg.rawbytes()[self._BREAKPOINT:]

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


bdn_performance_stats_message_converter_v14 = _BdnPerformanceStatsMessageConverterV14()
