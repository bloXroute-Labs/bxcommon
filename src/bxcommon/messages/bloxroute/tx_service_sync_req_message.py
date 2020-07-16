import struct
from typing import Optional

from bxcommon import constants
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType


class TxServiceSyncReqMessage(AbstractBloxrouteMessage):
    """
    Request for tx services sync
    """
    MESSAGE_TYPE = BloxrouteMessageType.TX_SERVICE_SYNC_REQ

    def __init__(self, network_num: Optional[int] = None, buf: Optional[bytearray] = None) -> None:
        if buf is None and network_num is not None:
            buf = bytearray(self.HEADER_LENGTH + constants.NETWORK_NUM_LEN + constants.CONTROL_FLAGS_LEN)
            self.buf = buf
            off = self.HEADER_LENGTH
            struct.pack_into("<L", self.buf, off, network_num)
            off += constants.NETWORK_NUM_LEN

        # pyre-fixme[8]: Attribute has type `bytearray`; used as `Optional[bytearray]`.
        self.buf: bytearray = buf
        self._network_num: Optional[int] = None

        super(TxServiceSyncReqMessage, self).__init__(
            self.MESSAGE_TYPE,
            len(self.buf) - self.HEADER_LENGTH,
            self.buf
        )

    def network_num(self) -> int:
        if self._network_num is None:
            off = self.HEADER_LENGTH
            self._network_num, = struct.unpack_from("<L", self._memoryview, off)

        network_num = self._network_num
        assert network_num is not None
        return network_num

    def __repr__(self) -> str:
        return "{}<network_num: {}".format(self.__class__.__name__, self.network_num())
