from datetime import datetime

from bxcommon.utils.log_level import LogLevel
from bxcommon.utils.message_buffer_builder import PayloadElement, PayloadBlock
from bxcommon.constants import HDR_COMMON_OFF
from bxcommon.messages.bloxroute.message import Message
from bxcommon.messages.bloxroute.protocol_version import PROTOCOL_VERSION


class KeepAliveMessage(Message):
    """
    BloXroute Version message that contains a message nonce to be used in the response.

    nonce: long, to be provided and managed by the connection
    """
    KEEP_ALIVE_MESSAGE_BLOCK = PayloadBlock(Message.HEADER_LENGTH, "ResponseMessage", PROTOCOL_VERSION,
                                            PayloadElement(name="nonce", structure="<Q",
                                                           decode=lambda x: x or None),
                                            )
    KEEP_ALIVE_MESSAGE_LENGTH = KEEP_ALIVE_MESSAGE_BLOCK.size

    def __init__(self, msg_type, nonce=None, buf=None):
        self.timestamp = datetime.utcnow()
        if buf is None:
            buf = bytearray(HDR_COMMON_OFF + self.KEEP_ALIVE_MESSAGE_LENGTH)

        buf = self.KEEP_ALIVE_MESSAGE_BLOCK.build(buf, nonce=nonce)

        self.buf = buf
        self._nonce = None
        self._network_num = None
        self._memoryview = memoryview(buf)
        super(KeepAliveMessage, self).__init__(msg_type, self.KEEP_ALIVE_MESSAGE_LENGTH, buf)

    def __unpack(self):
        contents = self.KEEP_ALIVE_MESSAGE_BLOCK.read(self._memoryview)
        self._nonce = contents.get("nonce")

    def nonce(self):
        if self._nonce is None:
            self.__unpack()
        return self._nonce

    def log_level(self):
        return LogLevel.INFO
