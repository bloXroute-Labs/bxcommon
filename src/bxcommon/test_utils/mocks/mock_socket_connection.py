import socket
from typing import Dict, Tuple, Any

from mock import MagicMock

from bxcommon.network.socket_connection import SocketConnection


class MockSocketConnection(SocketConnection):
    def __init__(self, fileno=1, node=None, default_socket_opts=None, send_bytes=False):
        super(MockSocketConnection, self).__init__(MagicMock(spec=socket.socket), node)

        if default_socket_opts is None:
            default_socket_opts = {
                (socket.SOL_SOCKET, socket.SO_SNDBUF): 4096
            }

        self._fileno = fileno
        # TODO: temporary fix for some situations where, see https://bloxroute.atlassian.net/browse/BX-1153
        self._send_bytes = send_bytes

        self.socket_instance = MagicMock()

        self.bytes_sent = []
        self.socket_opts: Dict[Tuple[int, int], Any] = default_socket_opts

        self.socket_instance.send = self.socket_instance_send
        self.socket_instance.setsockopt = self.socket_instance_set_opt
        self.socket_instance.getsockopt = self.socket_instance_get_opt

    def fileno(self):
        return self._fileno

    # TODO: temporary fix for some situations where, see https://bloxroute.atlassian.net/browse/BX-1153
    def send(self):
        if self._node is None or not self._send_bytes:
            return
        else:
            super().send()

    def socket_instance_send(self, bytes_written):
        if isinstance(bytes_written, memoryview):
            bytes_written = bytearray(bytes_written.tobytes())
        self.bytes_sent.append(bytes_written)
        return len(bytes_written)

    def socket_instance_get_opt(self, level: int, opt_name: int):
        return self.socket_opts[(level, opt_name)]

    def socket_instance_set_opt(self, level: int, opt_name: int, value: Any):
        self.socket_opts[(level, opt_name)] = value



