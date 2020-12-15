import struct
from datetime import datetime
from typing import Optional, Dict

from dataclasses import dataclass

from bxcommon import constants
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.network.ip_endpoint import IpEndpoint
from bxcommon.utils.stats import message_utils
from bxutils.logging import LogLevel
from bxutils import logging

logger = logging.get_logger(__name__)

@dataclass
class BdnPerformanceStatsData:
    new_blocks_received_from_blockchain_node: int = 0
    new_blocks_received_from_bdn: int = 0
    new_blocks_seen: int = 0

    # block_messages vs. block_announcements might not be a distinction that
    # exists in all blockchains. For example, in Ethereum this is the
    # distinction between NewBlock and NewBlockHashes messages
    new_block_messages_from_blockchain_node: int = 0
    new_block_announcements_from_blockchain_node: int = 0

    new_tx_received_from_blockchain_node: int = 0
    new_tx_received_from_bdn: int = 0
    new_tx_received_from_blockchain_node_low_fee: int = 0  # not sent in msg
    new_tx_received_from_bdn_low_fee: int = 0  # not sent in msg

    tx_sent_to_node: int = 0
    duplicate_tx_from_node: int = 0


class BdnPerformanceStatsMessage(AbstractBloxrouteMessage):
    """
    Bloxroute message sent from gateway to relay that contains statistics on BDN performance.
    """
    MESSAGE_TYPE = BloxrouteMessageType.BDN_PERFORMANCE_STATS

    _interval_start_time: Optional[float] = None
    _interval_end_time: Optional[float] = None
    _memory_utilization_mb: Optional[int] = None
    _node_stats: Optional[Dict[IpEndpoint, BdnPerformanceStatsData]] = None

    def __init__(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        memory_utilization_mb: Optional[int] = None,
        node_stats: Optional[Dict[IpEndpoint, BdnPerformanceStatsData]] = None,
        buf: Optional[bytearray] = None
    ):
        self.node_stats_offset = (
            AbstractBloxrouteMessage.HEADER_LENGTH
            + (1 * constants.UL_SHORT_SIZE_IN_BYTES)
            + (2 * constants.DOUBLE_SIZE_IN_BYTES)
        )

        if buf is None:
            assert start_time is not None
            assert end_time is not None
            assert memory_utilization_mb is not None
            assert node_stats is not None
            buf = self._serialize(start_time, end_time, memory_utilization_mb, node_stats)

        self.buf = buf
        payload_length = len(buf) - AbstractBloxrouteMessage.HEADER_LENGTH
        super().__init__(self.MESSAGE_TYPE, payload_length, self.buf)

    def log_level(self) -> LogLevel:
        return LogLevel.DEBUG

    def interval_start_time(self) -> datetime:
        if self._interval_start_time is None:
            self._unpack()

        interval_start_time = self._interval_start_time
        assert interval_start_time is not None
        return datetime.fromtimestamp(interval_start_time)

    def interval_end_time(self) -> datetime:
        if self._interval_end_time is None:
            self._unpack()

        interval_end_time = self._interval_end_time
        assert interval_end_time is not None
        return datetime.fromtimestamp(interval_end_time)

    def memory_utilization(self) -> int:
        if self._memory_utilization_mb is None:
            self._unpack()

        memory_utilization_mb = self._memory_utilization_mb
        assert memory_utilization_mb is not None
        return memory_utilization_mb

    def node_stats(self) -> Dict[IpEndpoint, BdnPerformanceStatsData]:
        if self._node_stats is None:
            self._unpack()

        node_stats = self._node_stats
        assert node_stats is not None
        return node_stats

    def _serialize(
        self,
        start_time: datetime,
        end_time: datetime,
        memory_utilization_mb: int,
        node_stats: Dict[IpEndpoint, BdnPerformanceStatsData]
    ):
        stats_serialized_length = constants.UL_SHORT_SIZE_IN_BYTES + len(node_stats) * (
            constants.IP_ADDR_SIZE_IN_BYTES +
            constants.UL_SHORT_SIZE_IN_BYTES +
            (2 * constants.UL_SHORT_SIZE_IN_BYTES) +
            (7 * constants.UL_INT_SIZE_IN_BYTES)
        )
        msg_size = (
            self.node_stats_offset
            + stats_serialized_length
            + constants.CONTROL_FLAGS_LEN
        )
        buf = bytearray(msg_size)
        off = AbstractBloxrouteMessage.HEADER_LENGTH

        struct.pack_into("<d", buf, off, start_time.timestamp())
        off += constants.DOUBLE_SIZE_IN_BYTES

        struct.pack_into("<d", buf, off, end_time.timestamp())
        off += constants.DOUBLE_SIZE_IN_BYTES

        memory_utilization_mb = min(memory_utilization_mb, constants.UNSIGNED_SHORT_MAX_VALUE)
        struct.pack_into("<H", buf, off, memory_utilization_mb)
        off += constants.UL_SHORT_SIZE_IN_BYTES

        struct.pack_into("<H", buf, off, len(node_stats))
        off += constants.UL_SHORT_SIZE_IN_BYTES

        for endpoint, node_stat in node_stats.items():
            message_utils.pack_ip_port(buf, off, endpoint.ip_address, endpoint.port)
            off += constants.IP_ADDR_SIZE_IN_BYTES + constants.UL_SHORT_SIZE_IN_BYTES

            struct.pack_into("<H", buf, off, node_stat.new_blocks_received_from_blockchain_node)
            off += constants.UL_SHORT_SIZE_IN_BYTES

            struct.pack_into("<H", buf, off, node_stat.new_blocks_received_from_bdn)
            off += constants.UL_SHORT_SIZE_IN_BYTES

            struct.pack_into("<I", buf, off, node_stat.new_tx_received_from_blockchain_node)
            off += constants.UL_INT_SIZE_IN_BYTES

            struct.pack_into("<I", buf, off, node_stat.new_tx_received_from_bdn)
            off += constants.UL_INT_SIZE_IN_BYTES

            struct.pack_into("<I", buf, off, node_stat.new_blocks_seen)
            off += constants.UL_INT_SIZE_IN_BYTES

            struct.pack_into("<I", buf, off, node_stat.new_block_messages_from_blockchain_node)
            off += constants.UL_INT_SIZE_IN_BYTES

            struct.pack_into("<I", buf, off, node_stat.new_block_announcements_from_blockchain_node)
            off += constants.UL_INT_SIZE_IN_BYTES

            struct.pack_into("<I", buf, off, node_stat.tx_sent_to_node)
            off += constants.UL_INT_SIZE_IN_BYTES

            struct.pack_into("<I", buf, off, node_stat.duplicate_tx_from_node)
            off += constants.UL_INT_SIZE_IN_BYTES

        return buf

    def _unpack(self) -> None:
        buf = self.buf
        assert buf is not None
        node_stats = {}

        off = AbstractBloxrouteMessage.HEADER_LENGTH
        self._interval_start_time, = struct.unpack_from("<d", buf, off)
        off += constants.DOUBLE_SIZE_IN_BYTES
        self._interval_end_time, = struct.unpack_from("<d", buf, off)
        off += constants.DOUBLE_SIZE_IN_BYTES
        self._memory_utilization_mb, = struct.unpack_from("<H", buf, off)
        off += constants.UL_SHORT_SIZE_IN_BYTES

        num_peers, = struct.unpack_from("<H", buf, off)
        off += constants.UL_SHORT_SIZE_IN_BYTES
        for _ in range(num_peers):
            ip, port = message_utils.unpack_ip_port(self._memoryview[off:].tobytes())
            off += constants.IP_ADDR_SIZE_IN_BYTES + constants.UL_SHORT_SIZE_IN_BYTES
            single_node_stats = BdnPerformanceStatsData()
            single_node_stats.new_blocks_received_from_blockchain_node, = struct.unpack_from("<H", buf, off)
            off += constants.UL_SHORT_SIZE_IN_BYTES
            single_node_stats.new_blocks_received_from_bdn, = struct.unpack_from("<H", buf, off)
            off += constants.UL_SHORT_SIZE_IN_BYTES
            single_node_stats.new_tx_received_from_blockchain_node, = struct.unpack_from("<I", buf, off)
            off += constants.UL_INT_SIZE_IN_BYTES
            single_node_stats.new_tx_received_from_bdn, = struct.unpack_from("<I", buf, off)
            off += constants.UL_INT_SIZE_IN_BYTES
            single_node_stats.new_blocks_seen, = struct.unpack_from("<I", buf, off)
            off += constants.UL_INT_SIZE_IN_BYTES
            single_node_stats.new_block_messages_from_blockchain_node, = struct.unpack_from("<I", buf, off)
            off += constants.UL_INT_SIZE_IN_BYTES
            single_node_stats.new_block_announcements_from_blockchain_node, = struct.unpack_from("<I", buf, off)
            off += constants.UL_INT_SIZE_IN_BYTES
            single_node_stats.tx_sent_to_node, = struct.unpack_from("<I", buf, off)
            off += constants.UL_INT_SIZE_IN_BYTES
            single_node_stats.duplicate_tx_from_node, = struct.unpack_from("<I", buf, off)
            off += constants.UL_INT_SIZE_IN_BYTES
            node_stats[IpEndpoint(ip, port)] = single_node_stats
        self._node_stats = node_stats

    def __repr__(self) -> str:
        return (
            f"BdnPerformanceStatsMessage<"
            f"memory_utilization: {self.memory_utilization()}, "
            f"bdn_stats_per_node: {self.node_stats()}"
            f">"
        )
