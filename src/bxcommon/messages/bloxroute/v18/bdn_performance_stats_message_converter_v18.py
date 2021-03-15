import struct

from bxcommon import constants
from bxcommon.messages.abstract_internal_message import AbstractInternalMessage
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.messages.bloxroute.bdn_performance_stats_message import BdnPerformanceStatsMessage
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.v18.bdn_performance_stats_message_v18 import \
    BdnPerformanceStatsMessageV18
from bxcommon.messages.versioning.abstract_message_converter import AbstractMessageConverter


class _BdnPerformanceStatsMessageConverterV18(AbstractMessageConverter):
    _MSG_TYPE_TO_OLD_MSG_CLASS_MAPPING = {
        BloxrouteMessageType.BDN_PERFORMANCE_STATS: BdnPerformanceStatsMessageV18
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

    _MEMORY_UTILIZATION_BREAKPOINT = (
        _INTERVAL_TIMES_BREAKPOINT +
        constants.UL_SHORT_SIZE_IN_BYTES
    )
    _MEMORY_UTILIZATION_LENGTH = _MEMORY_UTILIZATION_BREAKPOINT - _INTERVAL_TIMES_BREAKPOINT

    _NUM_BLOCKCHAIN_PEERS_BREAKPOINT = (
        _MEMORY_UTILIZATION_BREAKPOINT +
        constants.UL_SHORT_SIZE_IN_BYTES
    )
    _NUM_BLOCKCHAIN_PEERS_LENGTH = constants.UL_SHORT_SIZE_IN_BYTES

    _FIRST_NODE_STATS_BREAKPOINT = (
        _NUM_BLOCKCHAIN_PEERS_BREAKPOINT +
        (2 * constants.UL_SHORT_SIZE_IN_BYTES) +
        (5 * constants.UL_INT_SIZE_IN_BYTES)
    )
    _NODE_STATS_LENGTH = _FIRST_NODE_STATS_BREAKPOINT - _NUM_BLOCKCHAIN_PEERS_BREAKPOINT

    _MESSAGE_LEN_WITHOUT_NODE_STATS = (
        _BASE_LENGTH +
        _INTERVAL_TIMES_LENGTH + _MEMORY_UTILIZATION_LENGTH + _NUM_BLOCKCHAIN_PEERS_LENGTH +
        constants.CONTROL_FLAGS_LEN
    )

    _OLD_MESSAGE_NODE_STATS_LEN = (
        constants.IP_ADDR_SIZE_IN_BYTES + constants.UL_SHORT_SIZE_IN_BYTES +
        (5 * constants.UL_INT_SIZE_IN_BYTES) +
        (2 * constants.UL_SHORT_SIZE_IN_BYTES)
    )
    _NEW_MESSAGE_NODE_STATS_LEN = (
        _OLD_MESSAGE_NODE_STATS_LEN +
        (2 * constants.UL_INT_SIZE_IN_BYTES)
    )
    _NODE_STATS_LENGTH_DIFFERENCE = _NEW_MESSAGE_NODE_STATS_LEN - _OLD_MESSAGE_NODE_STATS_LEN

    def convert_from_older_version(
        self, msg: AbstractInternalMessage
    ) -> AbstractInternalMessage:
        msg_type = msg.MESSAGE_TYPE

        if msg_type not in self._MSG_TYPE_TO_NEW_MSG_CLASS_MAPPING:
            raise ValueError(
                f"Tried to convert unexpected old message type from v18: {msg_type}"
            )
        if len(msg.rawbytes()) == self._MESSAGE_LEN_WITHOUT_NODE_STATS:
            # per Endpoint Stats is not available
            length_difference = 0
            new_message_len = self._MESSAGE_LEN_WITHOUT_NODE_STATS
            num_blockchain_peers = 0
        else:
            num_blockchain_peers, = struct.unpack_from("<I", msg.rawbytes(), self._MEMORY_UTILIZATION_BREAKPOINT)
            length_difference = self._NODE_STATS_LENGTH_DIFFERENCE * num_blockchain_peers
            new_message_len = self._MESSAGE_LEN_WITHOUT_NODE_STATS + \
                (num_blockchain_peers * self._NEW_MESSAGE_NODE_STATS_LEN)

        new_msg_class = self._MSG_TYPE_TO_NEW_MSG_CLASS_MAPPING[msg_type]
        new_payload_len = msg.payload_len() + length_difference

        new_msg_bytes = bytearray(new_message_len)
        new_msg_bytes[:self._NUM_BLOCKCHAIN_PEERS_BREAKPOINT] = msg.rawbytes()[:self._NUM_BLOCKCHAIN_PEERS_BREAKPOINT]
        new_msg_off = self._NUM_BLOCKCHAIN_PEERS_BREAKPOINT
        old_msg_off = self._NUM_BLOCKCHAIN_PEERS_BREAKPOINT
        default_new_stats = 0
        for _ in range(num_blockchain_peers):
            new_msg_bytes[new_msg_off:new_msg_off + self._OLD_MESSAGE_NODE_STATS_LEN] = \
                msg.rawbytes()[old_msg_off:old_msg_off + self._OLD_MESSAGE_NODE_STATS_LEN]
            new_msg_off += self._OLD_MESSAGE_NODE_STATS_LEN
            old_msg_off += self._OLD_MESSAGE_NODE_STATS_LEN

            struct.pack_into("<I", new_msg_bytes, new_msg_off, default_new_stats)
            new_msg_off += constants.UL_INT_SIZE_IN_BYTES
            struct.pack_into("<I", new_msg_bytes, new_msg_off, default_new_stats)
            new_msg_off += constants.UL_INT_SIZE_IN_BYTES

        new_msg_bytes[new_msg_off:] = msg.rawbytes()[old_msg_off:]

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
        raise NotImplementedError


bdn_performance_stats_message_converter_v18 = _BdnPerformanceStatsMessageConverterV18()
