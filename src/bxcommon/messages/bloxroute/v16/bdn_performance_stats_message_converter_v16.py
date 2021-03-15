import struct

from bxcommon import constants
from bxcommon.messages.abstract_internal_message import AbstractInternalMessage
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.messages.bloxroute.bdn_performance_stats_message import BdnPerformanceStatsMessage
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.v16.bdn_performance_stats_message_v16 import \
    BdnPerformanceStatsMessageV16
from bxcommon.messages.versioning.abstract_message_converter import AbstractMessageConverter
from bxcommon.utils.stats import message_utils


class _BdnPerformanceStatsMessageConverterV16(AbstractMessageConverter):
    _MSG_TYPE_TO_OLD_MSG_CLASS_MAPPING = {
        BloxrouteMessageType.BDN_PERFORMANCE_STATS: BdnPerformanceStatsMessageV16
    }

    _MSG_TYPE_TO_NEW_MSG_CLASS_MAPPING = {
        BloxrouteMessageType.BDN_PERFORMANCE_STATS: BdnPerformanceStatsMessage
    }

    _BASE_LENGTH = (
        AbstractBloxrouteMessage.HEADER_LENGTH
    )

    _INTERVAL_TIMES_BREAKPOINT = (
        _BASE_LENGTH +
        (2 * constants.DOUBLE_SIZE_IN_BYTES)
    )
    _INTERVAL_TIMES_LENGTH = _INTERVAL_TIMES_BREAKPOINT - _BASE_LENGTH

    _FIRST_STATS_SETS_BREAKPOINT = (
        _INTERVAL_TIMES_BREAKPOINT +
        (2 * constants.UL_SHORT_SIZE_IN_BYTES) +
        (2 * constants.UL_INT_SIZE_IN_BYTES)
    )
    _FIRST_STATS_SETS_LENGTH = _FIRST_STATS_SETS_BREAKPOINT - _INTERVAL_TIMES_BREAKPOINT

    _MEMORY_UTILIZATION_BREAKPOINT = (
        _FIRST_STATS_SETS_BREAKPOINT +
        constants.UL_SHORT_SIZE_IN_BYTES
    )
    _MEMORY_UTILIZATION_LENGTH = _MEMORY_UTILIZATION_BREAKPOINT - _FIRST_STATS_SETS_BREAKPOINT

    _SECOND_STATS_SET_BREAKPOINT = (
        _MEMORY_UTILIZATION_BREAKPOINT +
        (3 * constants.UL_INT_SIZE_IN_BYTES)
    )
    _SECOND_STATS_SET_LENGTH = _SECOND_STATS_SET_BREAKPOINT - _MEMORY_UTILIZATION_BREAKPOINT

    _OLD_MESSAGE_LEN = BdnPerformanceStatsMessageV16.MSG_SIZE
    _NEW_MESSAGE_LEN = (
        BdnPerformanceStatsMessageV16.MSG_SIZE +
        constants.IP_ADDR_SIZE_IN_BYTES +
        (2 * constants.UL_SHORT_SIZE_IN_BYTES) +
        (2 * constants.UL_INT_SIZE_IN_BYTES)
    )
    _LENGTH_DIFFERENCE = _NEW_MESSAGE_LEN - _OLD_MESSAGE_LEN

    def convert_from_older_version(
        self, msg: AbstractInternalMessage
    ) -> AbstractInternalMessage:
        msg_type = msg.MESSAGE_TYPE

        if msg_type not in self._MSG_TYPE_TO_NEW_MSG_CLASS_MAPPING:
            raise ValueError(
                f"Tried to convert unexpected old message type from v16: {msg_type}"
            )

        new_msg_class = self._MSG_TYPE_TO_NEW_MSG_CLASS_MAPPING[msg_type]
        new_payload_len = msg.payload_len() + self._LENGTH_DIFFERENCE

        new_msg_bytes = bytearray(self._NEW_MESSAGE_LEN)
        new_msg_bytes[:self._INTERVAL_TIMES_BREAKPOINT] = msg.rawbytes()[:self._INTERVAL_TIMES_BREAKPOINT]
        off = self._BASE_LENGTH + self._INTERVAL_TIMES_LENGTH

        new_msg_bytes[off:off + self._MEMORY_UTILIZATION_LENGTH] = \
            msg.rawbytes()[
                self._FIRST_STATS_SETS_BREAKPOINT:self._FIRST_STATS_SETS_BREAKPOINT + self._MEMORY_UTILIZATION_LENGTH
            ]
        off += self._MEMORY_UTILIZATION_LENGTH

        # single blockchain peer
        struct.pack_into("<H", new_msg_bytes, off, 1)
        off += constants.UL_SHORT_SIZE_IN_BYTES

        # placeholder ip/port
        message_utils.pack_ip_port(new_msg_bytes, off, "0.0.0.0", 0)
        off += constants.IP_ADDR_SIZE_IN_BYTES + constants.UL_SHORT_SIZE_IN_BYTES

        new_msg_bytes[off:off + self._FIRST_STATS_SETS_LENGTH] = \
            msg.rawbytes()[
                self._INTERVAL_TIMES_BREAKPOINT:self._INTERVAL_TIMES_BREAKPOINT + self._FIRST_STATS_SETS_LENGTH
            ]
        off += self._FIRST_STATS_SETS_LENGTH

        new_msg_bytes[off:off + self._SECOND_STATS_SET_LENGTH] = \
            msg.rawbytes()[
                self._MEMORY_UTILIZATION_BREAKPOINT:self._MEMORY_UTILIZATION_BREAKPOINT + self._SECOND_STATS_SET_LENGTH
            ]
        off += self._SECOND_STATS_SET_LENGTH

        default_new_stats = 0
        struct.pack_into("<I", new_msg_bytes, off, default_new_stats)
        off += constants.UL_INT_SIZE_IN_BYTES
        struct.pack_into("<I", new_msg_bytes, off, default_new_stats)
        off += constants.UL_INT_SIZE_IN_BYTES

        new_msg_bytes[off:] = msg.rawbytes()[self._SECOND_STATS_SET_BREAKPOINT:]

        return AbstractBloxrouteMessage.initialize_class(
            new_msg_class,
            new_msg_bytes,
            (msg_type, new_payload_len)
        )

    def convert_to_older_version(
        self, msg: AbstractInternalMessage
    ) -> AbstractInternalMessage:
        # Message is one-way from gateway to relay, so converting from new to old version is not necessary.
        raise NotImplementedError

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
        # Message is one-way from gateway to relay, so converting from new to old version is not necessary.
        raise NotImplementedError

    def get_message_size_change_from_older_version(self) -> int:
        return self._LENGTH_DIFFERENCE


bdn_performance_stats_message_converter_v16 = _BdnPerformanceStatsMessageConverterV16()
