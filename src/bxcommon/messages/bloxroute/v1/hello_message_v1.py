import struct

from bxcommon.constants import HDR_COMMON_OFF, UL_INT_SIZE_IN_BYTES
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.message import Message


class HelloMessageV1(Message):
    """
    BloXroute hello message type.

    idx: index of the peer.
        Client will use 0 and will not be connected back to
        Other bloXroute servers send a positive identity specified in config file
    """
    MESSAGE_TYPE = BloxrouteMessageType.HELLO

    def __init__(self, idx=None, buf=None):

        if buf is None:
            buf = bytearray(HDR_COMMON_OFF + UL_INT_SIZE_IN_BYTES)
            self.buf = buf
            struct.pack_into("<L", buf, HDR_COMMON_OFF, idx)

            super(HelloMessageV1, self).__init__(self.MESSAGE_TYPE, UL_INT_SIZE_IN_BYTES, buf)
        else:
            self.buf = buf
            self._msg_type = self._payload_len = self._payload = None

        self._idx = None
        self._memoryview = memoryview(buf)

    def idx(self):
        if self._idx is None:
            off = HDR_COMMON_OFF
            self._idx, = struct.unpack_from("<L", self.buf, off)
        return self._idx
