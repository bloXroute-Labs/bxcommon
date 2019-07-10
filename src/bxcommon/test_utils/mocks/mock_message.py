from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage


class MockMessage(AbstractBloxrouteMessage):
    def __init__(self, msg_type=b"example", payload_len=0, buf=None):
        AbstractBloxrouteMessage.__init__(self, msg_type=msg_type, payload_len=payload_len, buf=buf)
