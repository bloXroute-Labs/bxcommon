import struct
from datetime import datetime

from bxcommon import constants
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxutils.logging import LogLevel


class BdnPerformanceStatsMessage(AbstractBloxrouteMessage):
    """
    Bloxroute message sent from gateway to relay that contains statistics on BDN performance.
    """

    MSG_SIZE = AbstractBloxrouteMessage.HEADER_LENGTH + (2 * constants.DOUBLE_SIZE_IN_BYTES) + \
               (4 * constants.UL_SHORT_SIZE_IN_BYTES) + constants.CONTROL_FLAGS_LEN
    MESSAGE_TYPE = BloxrouteMessageType.BDN_PERFORMANCE_STATS

    def __init__(self, start_time: datetime = None, end_time: datetime = None,
                 new_blocks_received_from_blockchain_node: int = None, new_blocks_received_from_bdn: int = None,
                 new_tx_received_from_blockchain_node: int = None, new_tx_received_from_bdn: int = None, buf=None):
        if buf is None:
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

            struct.pack_into("<H", buf, off, new_tx_received_from_blockchain_node)
            off += constants.UL_SHORT_SIZE_IN_BYTES

            struct.pack_into("<H", buf, off, new_tx_received_from_bdn)
            off += constants.UL_SHORT_SIZE_IN_BYTES

        self.buf = buf
        payload_length = len(self.buf) - AbstractBloxrouteMessage.HEADER_LENGTH
        super().__init__(self.MESSAGE_TYPE, payload_length, self.buf)

        self._interval_start_time = None
        self._interval_end_time = None
        self._new_blocks_received_from_blockchain_node = None
        self._new_blocks_received_from_bdn = None
        self._new_tx_received_from_blockchain_node = None
        self._new_tx_received_from_bdn = None

    def log_level(self):
        return LogLevel.DEBUG

    def interval_start_time(self) -> datetime:
        if self._interval_start_time is None:
            self._unpack()
        assert self._interval_start_time is not None
        return datetime.fromtimestamp(self._interval_start_time)

    def interval_end_time(self) -> datetime:
        if self._interval_end_time is None:
            self._unpack()
        assert self._interval_end_time is not None
        return datetime.fromtimestamp(self._interval_end_time)

    def new_blocks_from_blockchain_node(self) -> int:
        if self._new_blocks_received_from_blockchain_node is None:
            self._unpack()
        assert self._new_blocks_received_from_blockchain_node is not None
        return self._new_blocks_received_from_blockchain_node

    def new_blocks_from_bdn(self) -> int:
        if self._new_blocks_received_from_bdn is None:
            self._unpack()
        assert self._new_blocks_received_from_bdn is not None
        return self._new_blocks_received_from_bdn

    def new_tx_from_blockchain_node(self) -> int:
        if self._new_tx_received_from_blockchain_node is None:
            self._unpack()
        assert self._new_tx_received_from_blockchain_node is not None
        return self._new_tx_received_from_blockchain_node

    def new_tx_from_bdn(self) -> int:
        if self._new_tx_received_from_bdn is None:
            self._unpack()
        assert self._new_tx_received_from_bdn is not None
        return self._new_tx_received_from_bdn

    def _unpack(self):
        off = AbstractBloxrouteMessage.HEADER_LENGTH
        self._interval_start_time, = struct.unpack_from("<d", self.buf, off)
        off += constants.DOUBLE_SIZE_IN_BYTES
        self._interval_end_time, = struct.unpack_from("<d", self.buf, off)
        off += constants.DOUBLE_SIZE_IN_BYTES
        self._new_blocks_received_from_blockchain_node, = struct.unpack_from("<H", self.buf, off)
        off += constants.UL_SHORT_SIZE_IN_BYTES
        self._new_blocks_received_from_bdn, = struct.unpack_from("<H", self.buf, off)
        off += constants.UL_SHORT_SIZE_IN_BYTES
        self._new_tx_received_from_blockchain_node, = struct.unpack_from("<H", self.buf, off)
        off += constants.UL_SHORT_SIZE_IN_BYTES
        self._new_tx_received_from_bdn, = struct.unpack_from("<H", self.buf, off)
        off += constants.UL_SHORT_SIZE_IN_BYTES

    def __repr__(self):
        return "BdnPerformanceStatsMessage<blocks_from_blockchain_node: {}, blocks_from_bdn: {}, " \
               "tx_from_blockchain_node: {}, tx_from_bdn: {}>". \
            format(self.new_blocks_from_blockchain_node(), self.new_blocks_from_bdn(),
                   self.new_tx_from_blockchain_node(), self.new_tx_from_bdn())
