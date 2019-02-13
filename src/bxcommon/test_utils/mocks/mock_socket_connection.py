import socket

from mock import MagicMock

from bxcommon.network.socket_connection import SocketConnection


class MockSocketConnection(SocketConnection):
    def __init__(self, fileno=1, node=None):
        super(MockSocketConnection, self).__init__(MagicMock(spec=socket.socket), node)
        self._fileno = fileno

        self.socket_instance = MagicMock()
        self.bytes_sent = []
        self.socket_instance.send = self.socket_instance_send

    def fileno(self):
        return self._fileno

    def socket_instance_send(self, bytes_written):
        if isinstance(bytes_written, memoryview):
            bytes_written = bytearray(bytes_written.tobytes())
        self.bytes_sent.append(bytes_written)
        return len(bytes_written)

