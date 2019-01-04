from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.keep_alive_message import KeepAliveMessage


class PingMessage(KeepAliveMessage):
    MESSAGE_TYPE = BloxrouteMessageType.PING

    def __init__(self, buf=None):
        KeepAliveMessage.__init__(self, msg_type=self.MESSAGE_TYPE, buf=buf)

