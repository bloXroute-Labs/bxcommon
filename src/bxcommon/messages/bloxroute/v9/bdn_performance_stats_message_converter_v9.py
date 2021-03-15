import struct

from bxcommon import constants
from bxcommon.messages.abstract_internal_message import AbstractInternalMessage
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.messages.bloxroute.bdn_performance_stats_message import BdnPerformanceStatsMessage
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.v9.bdn_performance_stats_message_v9 import BdnPerformanceStatsMessageV9
from bxcommon.messages.versioning.abstract_message_converter import AbstractMessageConverter
from bxcommon.utils.stats import message_utils


class _BdnPerformanceStatsMessageConverterV9(AbstractMessageConverter):
    _MSG_TYPE_TO_OLD_MSG_CLASS_MAPPING = {
        BloxrouteMessageType.BDN_PERFORMANCE_STATS: BdnPerformanceStatsMessageV9
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

    _BLOCK_STATS_BREAKPOINT = (
        _INTERVAL_TIMES_BREAKPOINT +
        (2 * constants.UL_SHORT_SIZE_IN_BYTES)
    )
    _BLOCK_STATS_LENGTH = _BLOCK_STATS_BREAKPOINT - _INTERVAL_TIMES_BREAKPOINT

    _TX_STATS_BREAKPOINT = (
        _BLOCK_STATS_BREAKPOINT +
        (2 * constants.UL_SHORT_SIZE_IN_BYTES)
    )
    _TX_STATS_LENGTH = _TX_STATS_BREAKPOINT - _BLOCK_STATS_BREAKPOINT

    _OLD_MESSAGE_LEN = (
        BdnPerformanceStatsMessageV9.MSG_SIZE
    )

    _NEW_MESSAGE_LEN = (
        BdnPerformanceStatsMessageV9.MSG_SIZE +
        constants.UL_SHORT_SIZE_IN_BYTES +                                              # memory
        (2 * (constants.UL_INT_SIZE_IN_BYTES - constants.UL_SHORT_SIZE_IN_BYTES)) +     # new length of tx fields
        (5 * constants.UL_INT_SIZE_IN_BYTES) +                                          # new stats
        constants.IP_ADDR_SIZE_IN_BYTES +                                               # blockchain ip
        (2 * constants.UL_SHORT_SIZE_IN_BYTES)                                          # port, num blockchain peers
    )

    _LENGTH_DIFFERENCE = _NEW_MESSAGE_LEN - _OLD_MESSAGE_LEN

    def convert_from_older_version(
        self, msg: AbstractInternalMessage
    ) -> AbstractInternalMessage:
        msg_type = msg.MESSAGE_TYPE

        if msg_type not in self._MSG_TYPE_TO_NEW_MSG_CLASS_MAPPING:
            raise ValueError(
                f"Tried to convert unexpected old message type from v9: {msg_type}"
            )

        new_msg_class = self._MSG_TYPE_TO_NEW_MSG_CLASS_MAPPING[msg_type]
        new_payload_len = msg.payload_len() + self._LENGTH_DIFFERENCE

        default_new_stats = 0
        new_msg_bytes = bytearray(self._NEW_MESSAGE_LEN)
        new_msg_bytes[:self._INTERVAL_TIMES_BREAKPOINT] = msg.rawbytes()[:self._INTERVAL_TIMES_BREAKPOINT]
        off = self._BASE_LENGTH + self._INTERVAL_TIMES_LENGTH

        # memory
        struct.pack_into("<H", new_msg_bytes, off, default_new_stats)
        off += constants.UL_SHORT_SIZE_IN_BYTES

        # single blockchain peer
        struct.pack_into("<H", new_msg_bytes, off, 1)
        off += constants.UL_SHORT_SIZE_IN_BYTES

        # placeholder ip/port
        message_utils.pack_ip_port(new_msg_bytes, off, "0.0.0.0", 0)
        off += constants.IP_ADDR_SIZE_IN_BYTES + constants.UL_SHORT_SIZE_IN_BYTES

        new_msg_bytes[off:off + self._BLOCK_STATS_LENGTH] = \
            msg.rawbytes()[
            self._INTERVAL_TIMES_BREAKPOINT:self._INTERVAL_TIMES_BREAKPOINT + self._BLOCK_STATS_LENGTH
            ]
        off += self._BLOCK_STATS_LENGTH

        tx_received_from_blockchain_node, = struct.unpack_from(
            "<H", msg.rawbytes(), self._BLOCK_STATS_BREAKPOINT)
        tx_received_from_bdn, = struct.unpack_from(
            "<H", msg.rawbytes(), self._BLOCK_STATS_BREAKPOINT + constants.UL_SHORT_SIZE_IN_BYTES
        )

        # tx stats
        struct.pack_into("<I", new_msg_bytes, off, tx_received_from_blockchain_node)
        off += constants.UL_INT_SIZE_IN_BYTES
        struct.pack_into("<I", new_msg_bytes, off, tx_received_from_bdn)
        off += constants.UL_INT_SIZE_IN_BYTES

        struct.pack_into("<I", new_msg_bytes, off, default_new_stats)
        off += constants.UL_INT_SIZE_IN_BYTES
        struct.pack_into("<I", new_msg_bytes, off, default_new_stats)
        off += constants.UL_INT_SIZE_IN_BYTES
        struct.pack_into("<I", new_msg_bytes, off, default_new_stats)
        off += constants.UL_INT_SIZE_IN_BYTES
        struct.pack_into("<I", new_msg_bytes, off, default_new_stats)
        off += constants.UL_INT_SIZE_IN_BYTES
        struct.pack_into("<I", new_msg_bytes, off, default_new_stats)
        off += constants.UL_INT_SIZE_IN_BYTES

        new_msg_bytes[off:] = msg.rawbytes()[self._TX_STATS_BREAKPOINT:]

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
        return -self._LENGTH_DIFFERENCE

    def get_message_size_change_from_older_version(self) -> int:
        return self._LENGTH_DIFFERENCE


bdn_performance_stats_message_converter_v9 = _BdnPerformanceStatsMessageConverterV9()
