from bxcommon.constants import HDR_COMMON_OFF
from bxcommon.messages.bloxroute.message import Message


class KeepAliveMessage(Message):
    def __init__(self, msg_type=None, buf=None):
        if buf is None:
            buf = bytearray(HDR_COMMON_OFF)

            # Payload len = off - HDR_COMMON_OFF = 0
            Message.__init__(self, msg_type=msg_type, payload_len=0, buf=buf)
        else:
            self.buf = buf
            self._memoryview = memoryview(buf)
            self._nonce = self._command = self._payload_len = None
