from bxcommon import constants
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType


class AckMessage(AbstractBloxrouteMessage):
    MESSAGE_TYPE = BloxrouteMessageType.ACK

    def __init__(self, buf=None) -> None:
        if buf is None:
            buf = bytearray(self.HEADER_LENGTH + constants.CONTROL_FLAGS_LEN)
            self.buf = buf

            super(AckMessage, self).__init__(self.MESSAGE_TYPE, constants.CONTROL_FLAGS_LEN, buf)
        else:
            self.buf = buf
            self._memoryview = memoryview(self.buf)
            self._command = self._payload_len = None
            self._payload = None
