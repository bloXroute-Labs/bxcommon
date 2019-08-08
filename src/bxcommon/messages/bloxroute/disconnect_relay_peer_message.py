from bxcommon import constants
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType


class DisconnectRelayPeerMessage(AbstractBloxrouteMessage):
    MESSAGE_TYPE = BloxrouteMessageType.DISCONNECT_RELAY_PEER

    def __init__(self, buf=None):
        if buf is None:
            buf = bytearray(constants.BX_HDR_COMMON_OFF)
            self.buf = buf

            super().__init__(self.MESSAGE_TYPE, 0, buf)
        else:
            self.buf = buf
            self._memoryview = memoryview(self.buf)
            self._command = self._payload_len = None
            self._payload = None
