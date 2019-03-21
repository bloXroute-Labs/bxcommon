from bxcommon.messages.bloxroute.message import Message


class MockMessage(Message):
    def __init__(self, msg_type=b"example", payload_len=0, buf=None):
        Message.__init__(self, msg_type=msg_type, payload_len=payload_len, buf=buf)
