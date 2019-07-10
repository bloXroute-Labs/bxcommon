from bxcommon.constants import BX_HDR_COMMON_OFF
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.v4.message_v4 import MessageV4


class AckMessageV4(MessageV4):
    MESSAGE_TYPE = BloxrouteMessageType.ACK

    def __init__(self, buf=None):
        if buf is None:
            buf = bytearray(BX_HDR_COMMON_OFF)
            self.buf = buf

            MessageV4.__init__(self, self.MESSAGE_TYPE, 0, buf)
        else:
            self.buf = buf
            self._memoryview = memoryview(self.buf)
            self._command = self._payload_len = None
            self._payload = None
