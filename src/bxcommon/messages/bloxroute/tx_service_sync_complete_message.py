import struct
from typing import Optional

from bxcommon.constants import UL_INT_SIZE_IN_BYTES, CONTROL_FLAGS_LEN
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxutils.logging.log_level import LogLevel


class TxServiceSyncCompleteMessage(AbstractBloxrouteMessage):
    MESSAGE_TYPE = BloxrouteMessageType.TX_SERVICE_SYNC_COMPLETE

    """
    Message is sent after complete synchronize all txs in a network
    """

    def __init__(self, network_num: Optional[int] = None, buf: Optional[bytearray] = None) -> None:
        if buf is None:
            buf = bytearray(self.HEADER_LENGTH + UL_INT_SIZE_IN_BYTES + CONTROL_FLAGS_LEN)

        self.buf: bytearray = buf

        off = self.HEADER_LENGTH
        if network_num is not None:
            struct.pack_into("<L", self.buf, off, network_num)

        self._network_num: Optional[int] = network_num

        super(TxServiceSyncCompleteMessage, self).__init__(
            self.MESSAGE_TYPE,
            len(self.buf) - self.HEADER_LENGTH,
            self.buf
        )

    def log_level(self) -> LogLevel:
        return LogLevel.DEBUG

    def network_num(self) -> int:
        if self._network_num is None:
            off = self.HEADER_LENGTH
            self._network_num, = struct.unpack_from("<L", self._memoryview, off)

        network_num = self._network_num
        assert network_num is not None
        return network_num

    def __repr__(self) -> str:
        return "{}<network_num: {}".format(self.__class__.__name__, self.network_num())
