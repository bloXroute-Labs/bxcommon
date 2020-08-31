from bxcommon import constants
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.messages.bloxroute.protocol_version import PROTOCOL_VERSION
from bxcommon.utils.message_buffer_builder import PayloadElement, PayloadBlock
from bxutils.logging import LogLevel


class KeepAliveMessage(AbstractBloxrouteMessage):
    """
    BloXroute Version message that contains a message nonce to be used in the response.

    nonce: long, to be provided and managed by the connection
    """
    KEEP_ALIVE_MESSAGE_BLOCK = PayloadBlock(AbstractBloxrouteMessage.HEADER_LENGTH, "ResponseMessage", PROTOCOL_VERSION,
                                            PayloadElement(name="nonce", structure="<Q",
                                                           decode=lambda x: x or None),
                                            )
    KEEP_ALIVE_MESSAGE_LENGTH = KEEP_ALIVE_MESSAGE_BLOCK.size + constants.CONTROL_FLAGS_LEN

    def __init__(self, msg_type, nonce=None, buf=None) -> None:
        if buf is None:
            buf = bytearray(self.HEADER_LENGTH + self.KEEP_ALIVE_MESSAGE_LENGTH)

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

    def log_level(self) -> LogLevel:
        return LogLevel.DEBUG
