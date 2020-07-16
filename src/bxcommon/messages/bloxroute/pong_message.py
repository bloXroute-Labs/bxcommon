from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.keep_alive_message import KeepAliveMessage


class PongMessage(KeepAliveMessage):
    MESSAGE_TYPE = BloxrouteMessageType.PONG

    def __init__(self, nonce=None, buf=None) -> None:
        super(PongMessage, self).__init__(msg_type=self.MESSAGE_TYPE, nonce=nonce, buf=buf)

    def __repr__(self) -> str:
        return "PongMessage<nonce: {}>".format(self.nonce())
