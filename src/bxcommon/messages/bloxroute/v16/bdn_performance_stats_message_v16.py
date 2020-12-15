import struct
from datetime import datetime
from typing import Optional

from bxcommon import constants
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxutils.logging import LogLevel


class BdnPerformanceStatsMessageV16(AbstractBloxrouteMessage):
    """
    Bloxroute message sent from gateway to relay that contains statistics on BDN performance.
    """

    MSG_SIZE = (
        AbstractBloxrouteMessage.HEADER_LENGTH
        + (2 * constants.DOUBLE_SIZE_IN_BYTES)
        + (3 * constants.UL_SHORT_SIZE_IN_BYTES)
        + (2 * constants.UL_INT_SIZE_IN_BYTES)
        + (3 * constants.UL_INT_SIZE_IN_BYTES)
        + constants.CONTROL_FLAGS_LEN
    )
    MESSAGE_TYPE = BloxrouteMessageType.BDN_PERFORMANCE_STATS

    _interval_start_time: Optional[float] = None
    _interval_end_time: Optional[float] = None
    _new_blocks_received_from_blockchain_node: Optional[int] = None
    _new_blocks_received_from_bdn: Optional[int] = None
    _new_tx_received_from_blockchain_node: Optional[int] = None
    _new_tx_received_from_bdn: Optional[int] = None
    _memory_utilization_mb: Optional[int] = None
    _new_blocks_seen: Optional[int] = None
    _new_block_messages_from_blockchain_node: Optional[int] = None
    _new_block_announcements_from_blockchain_node: Optional[int] = None

    def __init__(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        new_blocks_received_from_blockchain_node: Optional[int] = None,
        new_blocks_received_from_bdn: Optional[int] = None,
        new_tx_received_from_blockchain_node: Optional[int] = None,
        new_tx_received_from_bdn: Optional[int] = None,
        memory_utilization_mb: Optional[int] = None,
        new_blocks_seen: Optional[int] = None,
        new_block_messages_from_blockchain_node: Optional[int] = None,
        new_block_announcements_from_blockchain_node: Optional[int] = None,
        buf: Optional[bytearray] = None
    ):
        if buf is None:
            assert start_time is not None
            assert end_time is not None
            assert new_blocks_received_from_blockchain_node is not None
            assert new_blocks_received_from_bdn is not None
            assert new_tx_received_from_blockchain_node is not None
            assert new_tx_received_from_bdn is not None
            assert memory_utilization_mb is not None
            assert new_blocks_seen is not None
            assert new_block_messages_from_blockchain_node is not None
            assert new_block_announcements_from_blockchain_node is not None

            buf = bytearray(self.MSG_SIZE)

            off = AbstractBloxrouteMessage.HEADER_LENGTH
            struct.pack_into("<d", buf, off, start_time.timestamp())
            off += constants.DOUBLE_SIZE_IN_BYTES

            struct.pack_into("<d", buf, off, end_time.timestamp())
            off += constants.DOUBLE_SIZE_IN_BYTES

            struct.pack_into("<H", buf, off, new_blocks_received_from_blockchain_node)
            off += constants.UL_SHORT_SIZE_IN_BYTES

            struct.pack_into("<H", buf, off, new_blocks_received_from_bdn)
            off += constants.UL_SHORT_SIZE_IN_BYTES

            struct.pack_into("<I", buf, off, new_tx_received_from_blockchain_node)
            off += constants.UL_INT_SIZE_IN_BYTES

            struct.pack_into("<I", buf, off, new_tx_received_from_bdn)
            off += constants.UL_INT_SIZE_IN_BYTES

            memory_utilization_mb = min(memory_utilization_mb, constants.UNSIGNED_SHORT_MAX_VALUE)
            struct.pack_into("<H", buf, off, memory_utilization_mb)
            off += constants.UL_SHORT_SIZE_IN_BYTES

            struct.pack_into("<I", buf, off, new_blocks_seen)
            off += constants.UL_INT_SIZE_IN_BYTES

            struct.pack_into("<I", buf, off, new_block_messages_from_blockchain_node)
            off += constants.UL_INT_SIZE_IN_BYTES

            struct.pack_into("<I", buf, off, new_block_announcements_from_blockchain_node)
            off += constants.UL_INT_SIZE_IN_BYTES

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

    def new_blocks_from_blockchain_node(self) -> int:
        if self._new_blocks_received_from_blockchain_node is None:
            self._unpack()

        new_blocks_received_from_blockchain_node = self._new_blocks_received_from_blockchain_node
        assert new_blocks_received_from_blockchain_node is not None
        return new_blocks_received_from_blockchain_node

    def new_blocks_from_bdn(self) -> int:
        if self._new_blocks_received_from_bdn is None:
            self._unpack()

        new_blocks_received_from_bdn = self._new_blocks_received_from_bdn
        assert new_blocks_received_from_bdn is not None
        return new_blocks_received_from_bdn

    def new_tx_from_blockchain_node(self) -> int:
        if self._new_tx_received_from_blockchain_node is None:
            self._unpack()

        new_tx_received_from_blockchain_node = self._new_tx_received_from_blockchain_node
        assert new_tx_received_from_blockchain_node is not None
        return new_tx_received_from_blockchain_node

    def new_tx_from_bdn(self) -> int:
        if self._new_tx_received_from_bdn is None:
            self._unpack()

        new_tx_received_from_bdn = self._new_tx_received_from_bdn
        assert new_tx_received_from_bdn is not None
        return new_tx_received_from_bdn

    def memory_utilization(self) -> int:
        if self._memory_utilization_mb is None:
            self._unpack()

        memory_utilization_mb = self._memory_utilization_mb
        assert memory_utilization_mb is not None
        return memory_utilization_mb

    def new_blocks_seen(self) -> int:
        if self._new_blocks_seen is None:
            self._unpack()

        new_blocks_seen = self._new_blocks_seen
        assert new_blocks_seen is not None
        return new_blocks_seen

    def new_block_messages_from_blockchain_node(self) -> int:
        if self._new_block_messages_from_blockchain_node is None:
            self._unpack()

        new_block_messages_from_blockchain_node = self._new_block_messages_from_blockchain_node
        assert new_block_messages_from_blockchain_node is not None
        return new_block_messages_from_blockchain_node

    def new_block_announcements_from_blockchain_node(self) -> int:
        if self._new_block_announcements_from_blockchain_node is None:
            self._unpack()

        new_block_announcements_from_blockchain_node = self._new_block_announcements_from_blockchain_node
        assert new_block_announcements_from_blockchain_node is not None
        return new_block_announcements_from_blockchain_node

    def _unpack(self) -> None:
        buf = self.buf
        assert buf is not None

        off = AbstractBloxrouteMessage.HEADER_LENGTH
        self._interval_start_time, = struct.unpack_from("<d", buf, off)
        off += constants.DOUBLE_SIZE_IN_BYTES
        self._interval_end_time, = struct.unpack_from("<d", buf, off)
        off += constants.DOUBLE_SIZE_IN_BYTES
        self._new_blocks_received_from_blockchain_node, = struct.unpack_from("<H", buf, off)
        off += constants.UL_SHORT_SIZE_IN_BYTES
        self._new_blocks_received_from_bdn, = struct.unpack_from("<H", buf, off)
        off += constants.UL_SHORT_SIZE_IN_BYTES
        self._new_tx_received_from_blockchain_node, = struct.unpack_from("<I", buf, off)
        off += constants.UL_INT_SIZE_IN_BYTES
        self._new_tx_received_from_bdn, = struct.unpack_from("<I", buf, off)
        off += constants.UL_INT_SIZE_IN_BYTES
        self._memory_utilization_mb, = struct.unpack_from("<H", buf, off)
        off += constants.UL_SHORT_SIZE_IN_BYTES
        self._new_blocks_seen, = struct.unpack_from("<I", buf, off)
        off += constants.UL_INT_SIZE_IN_BYTES
        self._new_block_messages_from_blockchain_node, = struct.unpack_from("<I", buf, off)
        off += constants.UL_INT_SIZE_IN_BYTES
        self._new_block_announcements_from_blockchain_node, = struct.unpack_from("<I", buf, off)
        off += constants.UL_INT_SIZE_IN_BYTES

    def __repr__(self) -> str:
        return (
            f"BdnPerformanceStatsMessage<"
            f"blocks_from_blockchain_node: {self.new_blocks_from_blockchain_node()}, "
            f"blocks_from_bdn: {self.new_blocks_from_bdn()}, "
            f"tx_from_blockchain_node: {self.new_tx_from_blockchain_node()}, "
            f"tx_from_bdn: {self.new_tx_from_bdn()}, "
            f"memory_utilization: {self.memory_utilization()}, "
            f"new_blocks_seen: {self.new_blocks_seen()}, "
            f"new_block_messages: {self.new_block_messages_from_blockchain_node()}, "
            f"new_block_announcements: {self.new_block_announcements_from_blockchain_node()}"
            f">"
        )
