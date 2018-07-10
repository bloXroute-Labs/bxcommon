from bxcommon.constants import BTC_HDR_COMMON_OFF
from bxcommon.messages.btc.btc_message import BTCMessage


class GetAddrBTCMessage(BTCMessage):
    def __init__(self, magic=None, buf=None):
        if buf is None:
            # We only construct empty getaddr messages.
            buf = bytearray(BTC_HDR_COMMON_OFF)
            self.buf = buf

            BTCMessage.__init__(self, magic, 'getaddr', 0, buf)
        else:
            self.buf = buf
            self._memoryview = memoryview(buf)
            self._magic = self._command = self._payload_len = self._checksum = None
            self._payload = None