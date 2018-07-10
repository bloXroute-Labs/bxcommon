from bxcommon.messages.keep_alive_message import KeepAliveMessage


class PongMessage(KeepAliveMessage):
    def __init__(self):
        KeepAliveMessage.__init__(self, msg_type='ping')
