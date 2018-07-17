from bxcommon.network.socket_connection_state import SocketConnectionState


class SocketConnection(object):
    def __init__(self, socket_instance, is_server=False):
        self.socket_instance = socket_instance
        self.is_server = is_server

        self.state = SocketConnectionState.CONNECTING

        self.can_send = False

    def set_state(self, state):
        self.state |= state

    def id(self):
        return self.socket_instance.fileno()

    def close(self):
        self.socket_instance.close()
