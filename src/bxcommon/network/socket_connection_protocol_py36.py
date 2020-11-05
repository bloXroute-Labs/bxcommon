from asyncio import Protocol
from typing import Optional

from bxcommon.network.abstract_socket_connection_protocol import AbstractSocketConnectionProtocol
from bxcommon.network.ip_endpoint import IpEndpoint


class SocketConnectionProtocolPy36(AbstractSocketConnectionProtocol, Protocol):
    def __init__(
        self,
        # pyre-fixme[11]: Annotation `AbstractNode` is not defined as a type.
        node: "AbstractNode",
        endpoint: Optional[IpEndpoint] = None,
        is_ssl: bool = True,
    ):
        AbstractSocketConnectionProtocol.__init__(self, node, endpoint, is_ssl)

    def data_received(self, data: bytes) -> None:
        if self.is_receivable():
            self._node.on_bytes_received(self.file_no, data)

    def get_last_read_duration_ms(self) -> float:
        return 0

    def get_time_since_read_end_ms(self, end_time: float) -> float:
        return 0
