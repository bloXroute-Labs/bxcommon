import socket

from mock import MagicMock

from bxcommon.network.socket_connection import SocketConnection


class MockSocketConnection(SocketConnection):
    def __init__(self, fileno=1):
        super(MockSocketConnection, self).__init__(MagicMock(spec=socket.socket), None)
        self._fileno = fileno

    def fileno(self):
        return self._fileno

