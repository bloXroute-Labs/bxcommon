import struct

from bxcommon.constants import HDR_COMMON_OFF
from bxcommon.messages.message import Message


class KeepAliveMessage(Message):
    def __init__(self, msg_type=None, buf=None, nonce=None):
        if buf is None:
            buf = bytearray(HDR_COMMON_OFF + 8)
            off = HDR_COMMON_OFF
            struct.pack_into('<Q', buf, off, nonce)
            off += 8

            Message.__init__(self, msg_type=msg_type, payload_len=off - HDR_COMMON_OFF, buf=buf)
        else:
            self.buf = buf
            self._memoryview = memoryview(buf)
            self._nonce = self._command = self._payload_len = None

    def nonce(self):
        if self._nonce is None:
            off = HDR_COMMON_OFF
            self._nonce, = struct.unpack_from('<Q', self.buf, off)
        return self._nonce
