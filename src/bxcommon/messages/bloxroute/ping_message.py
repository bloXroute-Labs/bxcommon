from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.keep_alive_message import KeepAliveMessage


class PingMessage(KeepAliveMessage):
    MESSAGE_TYPE = BloxrouteMessageType.PING

    def __init__(self, nonce=None, buf=None) -> None:
        super(PingMessage, self).__init__(msg_type=self.MESSAGE_TYPE, nonce=nonce, buf=buf)

    def __repr__(self):
        return "PingMessage<nonce: {}>".format(self.nonce())
