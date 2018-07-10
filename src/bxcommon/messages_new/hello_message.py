import struct

from bxcommon.constants import HDR_COMMON_OFF
from bxcommon.messages_new.message import Message


class HelloMessage(Message):
    # idx is the index of the peer. Clients will use 0 for the index and will not be connected back to.
    # Other bloXroute servers will send a positive identity specified in the config file
    def __init__(self, idx=None, buf=None):

        if buf is None:
            buf = bytearray(HDR_COMMON_OFF + 4)
            self.buf = buf
            struct.pack_into('<L', buf, HDR_COMMON_OFF, idx)

            Message.__init__(self, 'hello', 4, buf)
        else:
            self.buf = buf
            self._msg_type = self._payload_len = self._payload = None

        self._idx = None
        self._memoryview = memoryview(buf)

    def idx(self):
        if self._idx is None:
            off = HDR_COMMON_OFF
            self._idx, = struct.unpack_from('<L', self.buf, off)
        return self._idx
