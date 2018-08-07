from bxcommon.network.socket_connection_state import SocketConnectionState


class SocketConnection(object):
    def __init__(self, socket_instance, is_server=False):
        self.socket_instance = socket_instance
        self.is_server = is_server

        self.state = SocketConnectionState.CONNECTING

        self.can_send = False

    def set_state(self, state):
        self.state |= state

    def fileno(self):
        return self.socket_instance.fileno()

    def close(self):
        self.set_state(SocketConnectionState.MARK_FOR_CLOSE)
        self.socket_instance.close()
