import random
import struct
import sys

from bxcommon.constants import BTC_HDR_COMMON_OFF
from bxcommon.messages.btc.btc_message import BTCMessage


class PingBTCMessage(BTCMessage):
    def __init__(self, magic=None, buf=None):
        if buf is None:
            buf = bytearray(BTC_HDR_COMMON_OFF + 8)
            self.buf = buf

            off = BTC_HDR_COMMON_OFF
            struct.pack_into('<Q', buf, off, random.randint(0, sys.maxint))
            off += 8

            BTCMessage.__init__(self, magic, 'ping', off - BTC_HDR_COMMON_OFF, buf)
        else:
            self.buf = buf
            self._memoryview = memoryview(buf)
            self._magic = self._command = self._payload_len = self._checksum = None
            self._payload = None

        self._nonce = None

    def nonce(self):
        if self._nonce is None:
            if len(self.buf) == BTC_HDR_COMMON_OFF:
                self._nonce = -1
            elif len(self.buf) == BTC_HDR_COMMON_OFF + 4:
                self._nonce = struct.unpack_from('<L', self.buf, BTC_HDR_COMMON_OFF)[0]
            else:
                self._nonce = struct.unpack_from('<Q', self.buf, BTC_HDR_COMMON_OFF)[0]
        return self._nonce
