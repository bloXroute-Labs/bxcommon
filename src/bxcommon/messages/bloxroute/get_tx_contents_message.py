import struct
from typing import Optional

from bxcommon import constants
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxutils.logging.log_level import LogLevel


class GetTxContentsMessage(AbstractBloxrouteMessage):
    MESSAGE_TYPE = BloxrouteMessageType.GET_TX_CONTENTS

    """
    Message used to request transaction contents.
    Node needs to reply with TxContentsMessage
    """

    def __init__(self, network_num: Optional[int] = None, short_id: Optional[int] = None,
                 buf: Optional[bytearray] = None):
        """
        Constructor. Expects network num and short id, or message bytes.

        :param network_num: blockchain network number
        :param short_id: short id
        :param buf: message bytes
        """
        msg_size = self.HEADER_LENGTH + constants.NETWORK_NUM_LEN + constants.SID_LEN + constants.CONTROL_FLAGS_LEN

        self._network_num = None
        self._short_id = None
        if buf is None:
            buf = bytearray(msg_size)
            off = self.HEADER_LENGTH

            struct.pack_into("<L", buf, off, network_num)
            off += constants.NETWORK_NUM_LEN
            struct.pack_into("<L", buf, off, short_id)
            off += constants.SID_LEN

            super(GetTxContentsMessage, self).__init__(self.MESSAGE_TYPE, msg_size - self.HEADER_LENGTH, buf)
        else:
            if isinstance(buf, str):
                raise TypeError("Buffer can't be string")

            self.buf = buf
            self._memoryview = memoryview(self.buf)
            self._payload_len = None
            self._payload = None

    def log_level(self):
        return LogLevel.DEBUG

    def network_num(self) -> int:
        if self._network_num is None:
            self._parse()

        assert self._network_num
        # pyre-fixme[7]: Expected `int` but got `None`.
        return self._network_num

    def get_short_id(self) -> int:
        if self._short_id is None:
            self._parse()

        assert self._short_id
        # pyre-fixme[7]: Expected `int` but got `None`.
        return self._short_id

    def _parse(self) -> None:
        off = self.HEADER_LENGTH

        self._network_num, = struct.unpack_from("<L", self.buf, off)
        off += constants.NETWORK_NUM_LEN

        self._short_id, = struct.unpack_from("<L", self.buf, off)
        off += constants.SID_LEN

    def __repr__(self):
        return f"GetTxContentsMessage<network_num: {self.network_num()}, short_id: {self.get_short_id()}>"
