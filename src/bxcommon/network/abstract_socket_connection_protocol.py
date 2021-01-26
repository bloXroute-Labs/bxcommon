import socket
import sys
import typing
from abc import abstractmethod
from asyncio import BaseTransport, Transport, BaseProtocol
from typing import TYPE_CHECKING, Optional

from cryptography.x509 import Certificate

from bxcommon.network.ip_endpoint import IpEndpoint
from bxcommon.network.network_direction import NetworkDirection
from bxcommon.network.socket_connection_state import SocketConnectionState, SocketConnectionStates
from bxcommon.utils.stats import hooks
from bxutils import logging
from bxutils.logging import LogRecordType
from bxutils.ssl import ssl_certificate_factory

if TYPE_CHECKING:
    # pylint: disable=ungrouped-imports,cyclic-import
    from bxcommon.connections.abstract_node import AbstractNode

logger = logging.get_logger(__name__)
network_troubleshooting_logger = logging.get_logger(LogRecordType.NetworkTroubleshooting, __name__)
SO_QUICKACK = 12


class AbstractSocketConnectionProtocol(BaseProtocol):
    transport: Optional[Transport]
    file_no: int
    endpoint: IpEndpoint
    direction: NetworkDirection
    can_send: bool
    state: SocketConnectionState
    is_ssl: bool

    _node: "AbstractNode"
    _should_retry: bool
    _receive_buf: bytearray

    # performance critical attributes, have been pulled out of state
    alive: bool
    initialized: bool

    def __init__(
        self,
        node: "AbstractNode",
        endpoint: Optional[IpEndpoint] = None,
        is_ssl: bool = True,
    ):
        self._node = node
        self.transport: Optional[Transport] = None
        self.file_no = -1
        # pyre-fixme[8]: Attribute has type `IpEndpoint`; used as
        #  `Optional[IpEndpoint]`.
        self.endpoint = endpoint
        if self.endpoint is None:
            self.direction = NetworkDirection.INBOUND
        else:
            self.direction = NetworkDirection.OUTBOUND
        self.can_send = False
        self.state = SocketConnectionStates.CONNECTING
        self.is_ssl = is_ssl
        self._should_retry = self.direction == NetworkDirection.OUTBOUND
        self._initial_bytes = None
        self._receive_buf = bytearray(node.opts.receive_buffer_size)

        self.alive = True
        self.initialized = False

    def __repr__(self) -> str:
        return f"{self.__class__.__name__} <{self.endpoint}, {self.direction.name}>"

    def connection_made(self, transport: BaseTransport) -> None:
        self.transport = typing.cast(Transport, transport)

        sock = transport.get_extra_info("socket")
        self.file_no = sock.fileno()
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

        if self._node.opts.enable_tcp_quickack:
            self.enable_tcp_quickack()

        if self.direction == NetworkDirection.INBOUND:
            self.endpoint = IpEndpoint(
                *transport.get_extra_info("peername")
            )
            logger.debug("[{}] - accepted connection.", self)

        self._node.on_connection_added(self)
        self.initialized = True
        self.can_send = True
        self.send()
        logger.debug("[{}] - connection established successfully.", self)

    def connection_lost(self, exc: Optional[Exception]) -> None:
        mark_for_close = self.alive
        self.alive = False
        if not self._should_retry:
            self.state |= SocketConnectionStates.DO_NOT_RETRY
        if exc is not None:
            logger.info(
                "[{}] - lost connection due to an error: {}, closing connection, should_retry: {}.",
                self,
                exc,
                self._should_retry,
            )
        else:
            logger.debug(
                "[{}] - lost connection with peer, should_retry: {}.",
                self,
                self._should_retry,
            )
        self._node.on_connection_closed(self.file_no, mark_for_close)

    def pause_writing(self) -> None:
        self.can_send = False
        logger.debug("[{}] - paused writing.", self)

    def resume_writing(self) -> None:
        self.can_send = True
        self.send()
        logger.debug("[{}] - resumed writing.", self)

    def send(self) -> None:
        # TODO: send should buffer together multiple pending buffers and write\
        #  them together to the Transport.
        total_bytes_sent = 0

        conn = self._node.connection_pool.get_by_fileno(self.file_no)

        if not conn:
            return

        while self.is_sendable():
            data = conn.get_bytes_to_send()
            if not data:
                break

            transport = self.transport
            assert transport is not None, "Connection is broken!"
            # note: transport.write() is non blocking and accepts any length of data
            #       even if data is crossing the buffer high limit (will cause a pause)
            bytes_to_send = len(data)
            # pyre-fixme[16]: `Transport` has no attribute `get_write_buffer_limits`.
            buffer_limits = transport.get_write_buffer_limits()
            logger.trace(
                "[{}] - about to send {} bytes, current buffer used {} with limits {}",
                self,
                bytes_to_send,
                transport.get_write_buffer_size(),
                buffer_limits
            )
            transport.write(data)
            conn.advance_sent_bytes(bytes_to_send)
            total_bytes_sent += bytes_to_send

        if total_bytes_sent:
            logger.trace("[{}] - sent {} bytes", self, total_bytes_sent)

    def send_bytes(self, bytes_to_send: typing.Union[memoryview, bytearray]):
        conn = self._node.connection_pool.get_by_fileno(self.file_no)

        if not conn:
            return

        transport = self.transport
        assert transport is not None, "Connection is broken!"

        # pyre-fixme[16]: `Transport` has no attribute `get_write_buffer_limits`.
        buffer_limits = transport.get_write_buffer_limits()
        logger.trace(
            "[{}] - about to send {} bytes, current buffer used {} with limits {}",
            self,
            bytes_to_send,
            transport.get_write_buffer_size(),
            buffer_limits
        )
        transport.write(bytes_to_send)
        len_bytes_to_sent = len(bytes_to_send)
        hooks.add_throughput_event(
            NetworkDirection.OUTBOUND,
            "outgoing",
            len_bytes_to_sent,
            conn.peer_desc,
            conn.peer_id
        )
        logger.trace("[{}] - sent {} bytes", self, len_bytes_to_sent)

    def pause_reading(self) -> None:
        if self.alive:
            assert self.transport is not None, "Connection is broken!"
            self.state |= SocketConnectionStates.HALT_RECEIVE
            logger.debug("[{}] - paused reading.", self)

    def resume_reading(self) -> None:
        if self.alive:
            assert self.transport is not None, "Connection is broken!"
            # pylint bug
            # pylint: disable=invalid-unary-operand-type
            self.state &= ~SocketConnectionStates.HALT_RECEIVE
            logger.debug("[{}] - resumed reading.", self)

    def mark_for_close(self, should_retry: bool = True) -> None:
        if not self.alive:
            return

        self.alive = False
        self._should_retry = should_retry

        transport = self.transport
        assert transport is not None, "Connection is broken!"
        # ideally this would be `transport.close()`, but buffers don't
        # seem to be flushing for 1+ days
        transport.abort()
        logger.debug(
            "[{}] - marked for close, retrying: {}.", self, should_retry
        )

    def is_receivable(self) -> bool:
        return (
            self.alive
            and SocketConnectionStates.HALT_RECEIVE not in self.state
        )

    def is_sendable(self) -> bool:
        """
        Returns if the socket has room on the buffer and can be sent to.

        This function is very frequently called. Avoid doing any sort of complex
        operations, inline function calls, and avoid flags.
        :return:
        """
        return self.alive and self.initialized and self.can_send

    def get_peer_certificate(self) -> Certificate:
        assert self.transport is not None, "Connection is broken!"
        try:
            return ssl_certificate_factory.get_transport_cert(self.transport)
        except ValueError as e:
            raise TypeError("Socket is not SSL type!") from e

    def get_write_buffer_size(self) -> int:
        transport = self.transport
        assert transport is not None, "Connection is broken!"
        if transport.is_closing():
            return 0
        else:
            return transport.get_write_buffer_size()

    def enable_tcp_quickack(self):
        if "linux" in sys.platform:
            sock = self.transport.get_extra_info("socket")
            if sock is None:
                logger.debug("Socket info is None on connection")
            else:
                sock.setsockopt(socket.SOL_SOCKET, SO_QUICKACK, 1)

    @abstractmethod
    def get_last_read_duration_ms(self) -> float:
        pass

    @abstractmethod
    def get_time_since_read_end_ms(self, end_time: float):
        pass
