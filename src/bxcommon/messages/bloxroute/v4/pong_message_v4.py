from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.v4.keep_alive_message_v4 import KeepAliveMessageV4


class PongMessageV4(KeepAliveMessageV4):
    MESSAGE_TYPE = BloxrouteMessageType.PONG

    def __init__(self, nonce=None, buf=None):
        super(PongMessageV4, self).__init__(msg_type=self.MESSAGE_TYPE, nonce=nonce, buf=buf)

    def __repr__(self):
        return "PongMessage<nonce: {}>".format(self.nonce())
