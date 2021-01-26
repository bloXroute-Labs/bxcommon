import socket
from typing import Dict, Tuple, Any

from mock import MagicMock

from bxcommon.connections.connection_type import ConnectionType
from bxcommon.models.authenticated_peer_info import AuthenticatedPeerInfo
from bxcommon.network.ip_endpoint import IpEndpoint
from bxcommon.network.socket_connection_protocol import SocketConnectionProtocol


class MockSocketConnection(SocketConnectionProtocol):
    def __init__(
        self,
        file_no,
        node,
        default_socket_opts=None,
        send_bytes=False,
        ip_address: str = "127.0.0.1",
        port: int = 8000,
        is_ssl: bool = False,
        authenticated_peer_info: AuthenticatedPeerInfo = AuthenticatedPeerInfo(
            ConnectionType.EXTERNAL_GATEWAY, "", ""
        ),
    ):
        super(MockSocketConnection, self).__init__(
            node, IpEndpoint(ip_address, port), is_ssl=is_ssl
        )
        self.transport = MagicMock()
        if default_socket_opts is None:
            default_socket_opts = {(socket.SOL_SOCKET, socket.SO_SNDBUF): 4096}

        self.file_no = file_no
        # TODO: temporary fix for some situations where, see https://bloxroute.atlassian.net/browse/BX-1153
        self._send_bytes = send_bytes

        self.bytes_sent = []
        self.socket_opts: Dict[Tuple[int, int], Any] = default_socket_opts

        self.transport.write = self.socket_instance_send
        self.transport.get_write_buffer_size = MagicMock(return_value=0)

        self.authenticated_peer_info = authenticated_peer_info
        self.initialized = True

    def fileno(self) -> int:
        return self.file_no

    # TODO: temporary fix for some situations where, see https://bloxroute.atlassian.net/browse/BX-1153
    def send(self) -> None:
        if self._node is None or not self._send_bytes:
            return
        else:
            super(MockSocketConnection, self).send()

    def socket_instance_send(self, bytes_written):
        if isinstance(bytes_written, memoryview):
            bytes_written = bytearray(bytes_written.tobytes())
        self.bytes_sent.append(bytes_written)
        return len(bytes_written)

    def socket_instance_get_opt(self, level: int, opt_name: int):
        return self.socket_opts[(level, opt_name)]

    def socket_instance_set_opt(self, level: int, opt_name: int, value: Any):
        self.socket_opts[(level, opt_name)] = value

    def mark_for_close(self, should_retry: bool = True) -> None:
        super(MockSocketConnection, self).mark_for_close(should_retry)
        self.connection_lost(None)

    def get_write_buffer_size(self) -> int:
        return 0
