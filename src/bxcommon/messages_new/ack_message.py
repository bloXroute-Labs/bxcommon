from bxcommon.constants import HDR_COMMON_OFF
from bxcommon.messages_new.message import Message


class AckMessage(Message):
    def __init__(self, buf=None):
        if buf is None:
            buf = bytearray(HDR_COMMON_OFF)
            self.buf = buf

            Message.__init__(self, 'ack', 0, buf)
        else:
            self.buf = buf
            self._memoryview = memoryview(buf)
            self._command = self._payload_len = None
            self._payload = None
