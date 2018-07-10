import struct

from bxcommon.constants import HDR_COMMON_OFF
from bxcommon.messages_new.message import Message


# XXX: Duplicated from Ping
class PongMessage(Message):
    def __init__(self, nonce=None, buf=None):
        if buf is None:
            buf = bytearray(HDR_COMMON_OFF + 8)
            off = HDR_COMMON_OFF
            struct.pack_into('<Q', buf, off, nonce)
            off += 8

            Message.__init__(self, 'pong', off - HDR_COMMON_OFF, buf)
        else:
            self.buf = buf
            self._memoryview = memoryview(buf)
            self._nonce = self._command = self._payload_len = None

    def nonce(self):
        if self._nonce is None:
            off = HDR_COMMON_OFF
            self._nonce, = struct.unpack_from('<Q', self.buf, off)
        return self._nonce
