from typing import Optional

from bxcommon import constants
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.keep_alive_message import KeepAliveMessage
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.messages.bloxroute.protocol_version import PROTOCOL_VERSION
from bxcommon.utils.message_buffer_builder import PayloadElement, PayloadBlock


class PongMessage(KeepAliveMessage):
    MESSAGE_TYPE = BloxrouteMessageType.PONG

    PONG_MESSAGE_BLOCK = PayloadBlock(
        AbstractBloxrouteMessage.HEADER_LENGTH,
        "ResponseMessage",
        PROTOCOL_VERSION,
        PayloadElement(name="nonce", structure="<Q", decode=lambda x: x or None),
        PayloadElement(name="timestamp", structure="<Q", decode=lambda x: x or None),
    )
    PONG_MESSAGE_LENGTH = PONG_MESSAGE_BLOCK.size + constants.CONTROL_FLAGS_LEN

    def __init__(
        self, nonce: Optional[int] = None, timestamp: Optional[int] = None, buf: Optional[bytearray] = None
    ) -> None:
        if buf is None:
            buf = bytearray(self.HEADER_LENGTH + self.PONG_MESSAGE_LENGTH)

        buf = self.PONG_MESSAGE_BLOCK.build(buf, timestamp=timestamp)

        self._timestamp: Optional[int] = None
        super(PongMessage, self).__init__(
            msg_type=self.MESSAGE_TYPE, nonce=nonce, buf=buf, payload_length=self.PONG_MESSAGE_LENGTH
        )

    def __unpack(self) -> None:
        contents = self.PONG_MESSAGE_BLOCK.read(self._memoryview)
        self._nonce = contents.get("nonce")
        self._timestamp = contents.get("timestamp")

    def timestamp(self) -> Optional[int]:
        if self._timestamp is None:
            self.__unpack()
        return self._timestamp

    def __repr__(self) -> str:
        return "PongMessage<nonce: {},timestamp: {}>".format(self.nonce(), self.timestamp())
