import typing
from asyncio import Protocol, BaseTransport, Transport
from typing import TYPE_CHECKING, Optional

from bxcommon.network.ip_endpoint import IpEndpoint
from bxcommon.network.network_direction import NetworkDirection
from bxcommon.network.socket_connection_state import SocketConnectionState

from bxutils import logging

if TYPE_CHECKING:
    from bxcommon.connections.abstract_node import AbstractNode

logger = logging.get_logger(__name__)


class SocketConnectionProtocol(Protocol):
    transport: Optional[Transport]
    file_no: int
    endpoint: IpEndpoint
    direction: NetworkDirection
    can_send: bool
    state: SocketConnectionState
    _node: "AbstractNode"
    _should_retry: bool

    def __init__(self, node: "AbstractNode", endpoint: Optional[IpEndpoint] = None):
        self._node = node
        self.transport: Optional[Transport] = None
        self.file_no = -1
        self.endpoint = endpoint
        if self.endpoint is None:
            self.direction = NetworkDirection.INBOUND
        else:
            self.direction = NetworkDirection.OUTBOUND
        self.can_send = False
        self.state = SocketConnectionState.CONNECTING
        self._should_retry = self.direction == NetworkDirection.OUTBOUND

    def __repr__(self) -> str:
        return f"{self.__class__.__name__} <{self.endpoint}, {self.direction.name}>"

    def data_received(self, data: bytes) -> None:
        self._node.on_bytes_received(self.file_no, data)

    def connection_made(self, transport: BaseTransport) -> None:
        self.transport = typing.cast(Transport, transport)
        self.file_no = self.transport.get_extra_info("socket").fileno()
        if self.direction == NetworkDirection.INBOUND:
            self.endpoint = IpEndpoint(*self.transport.get_extra_info("peername"))
            logger.debug("[{}] - accepted connection.", self)
        self._node.on_connection_added(self)
        self.state = SocketConnectionState.INITIALIZED
        self.can_send = True
        self.send()
        logger.debug("[{}] - connection established successfully.", self)

    def connection_lost(self, exc: Optional[Exception]) -> None:
        self.state |= SocketConnectionState.MARK_FOR_CLOSE
        if not self._should_retry:
            self.state |= SocketConnectionState.DO_NOT_RETRY
        if exc is not None:
            logger.info("[{}] - lost connection due to an error: {}, closing connection.", self, exc)
        else:
            logger.debug("[{}] - lost connection with peer, should_retry: {}.", self, self._should_retry)
        self._node.on_connection_closed(self.file_no)

    def pause_writing(self) -> None:
        self.can_send = False
        logger.trace("[{}] - paused writing.", self)

    def resume_writing(self) -> None:
        self.can_send = True
        self.send()
        logger.trace("[{}] - resumed writing.", self)

    def send(self) -> None:
        while self.state & SocketConnectionState.INITIALIZED and self.is_alive() and self.can_send:
            data = self._node.get_bytes_to_send(self.file_no)
            if not data:
                break
            assert self.transport is not None, "Connection is broken!"
            self.transport.write(data)
            self._node.on_bytes_sent(self.file_no, len(data))

    def pause_reading(self) -> None:
        if self.is_alive():
            assert self.transport is not None, "Connection is broken!"
            self.transport.pause_reading()
            logger.trace("[{}] - paused reading.", self)

    def resume_reading(self) -> None:
        if self.is_alive():
            assert self.transport is not None, "Connection is broken!"
            self.transport.resume_reading()
            logger.trace("[{}] - resumed writing.", self)

    def mark_for_close(self, should_retry: bool = True) -> None:
        self._should_retry = should_retry
        assert self.transport is not None, "Connection is broken!"
        self.transport.close()
        logger.debug("[{}] - marked for close, retrying: {}.", self, should_retry)

    def is_alive(self) -> bool:
        return not self.state & SocketConnectionState.MARK_FOR_CLOSE