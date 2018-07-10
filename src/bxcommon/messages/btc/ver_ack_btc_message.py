from bxcommon.constants import BTC_HDR_COMMON_OFF
from bxcommon.messages.btc.btc_message import BTCMessage


class VerAckBTCMessage(BTCMessage):
    def __init__(self, magic=None, buf=None):
        if buf is None:
            buf = bytearray(BTC_HDR_COMMON_OFF)
            self.buf = buf

            BTCMessage.__init__(self, magic, 'verack', 0, buf)
        else:
            self.buf = buf
            self._memoryview = memoryview(buf)
            self._magic = self._command = self._payload_len = self._checksum = None
            self._payload = None
