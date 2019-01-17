from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.v1.keep_alive_message_v1 import KeepAliveMessageV1


class PingMessageV1(KeepAliveMessageV1):
    MESSAGE_TYPE = BloxrouteMessageType.PING

    def __init__(self, buf=None):
        KeepAliveMessageV1.__init__(self, msg_type=self.MESSAGE_TYPE, buf=buf)
