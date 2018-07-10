from bxcommon.messages.keep_alive_message import KeepAliveMessage


class PongMessage(KeepAliveMessage):
    def __init__(self, nonce=None, buf=None):
        KeepAliveMessage.__init__(self, msg_type='pong', nonce=nonce, buf=buf)
