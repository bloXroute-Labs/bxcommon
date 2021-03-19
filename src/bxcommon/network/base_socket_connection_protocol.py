import sys
from asyncio import BaseProtocol, BaseTransport, Transport
from typing import Optional, TYPE_CHECKING

import typing

from bxcommon import constants
from bxcommon.network.abstract_socket_connection_protocol import AbstractSocketConnectionProtocol
from bxcommon.network.ip_endpoint import IpEndpoint
from bxcommon.network.socket_connection_protocol_py36 import SocketConnectionProtocolPy36
from bxutils import logging

if TYPE_CHECKING:
    # noinspection PyUnresolvedReferences
    # pylint: disable=ungrouped-imports,cyclic-import
    from bxcommon.connections.abstract_node import AbstractNode

logger = logging.get_logger(__name__)


class BaseSocketConnectionProtocol(BaseProtocol):
    _delegate_protocol: Optional[AbstractSocketConnectionProtocol]

    def __init__(
        self,
        node: "AbstractNode",
        endpoint: Optional[IpEndpoint] = None,
        is_ssl: bool = True,
    ):
        self._node = node
        self._endpoint = endpoint
        self._is_server = endpoint is None
        self._delegate_protocol = None
        self.is_ssl = is_ssl

    def __getattr__(self, item):
        delegate_protocol = self._delegate_protocol
        if delegate_protocol is not None:
            result = getattr(delegate_protocol, item)
            return result
        return None

    def connection_made(self, transport: BaseTransport) -> None:
        transport = typing.cast(Transport, transport)

        if self._endpoint is None:
            self._endpoint = IpEndpoint(*transport.get_extra_info("peername"))

        endpoint = self._endpoint
        assert endpoint is not None

        if self._is_server:
            attempts = self._node.report_connection_attempt(endpoint.ip_address)
            if attempts >= constants.MAX_HIGH_RECONNECT_ATTEMPTS_ALLOWED:
                logger.debug(
                    "Rejecting connection attempt from {}. Too many attempts: {}",
                    self._endpoint,
                    attempts
                )
                # transport.abort()
                # return

        if sys.version.startswith("3.6."):
            protocol_cls = SocketConnectionProtocolPy36
        else:
            from bxcommon.network.socket_connection_protocol import SocketConnectionProtocol
            protocol_cls = SocketConnectionProtocol

        if self._is_server:
            endpoint = None
        delegate_protocol = protocol_cls(self._node, endpoint, self.is_ssl)
        delegate_protocol.connection_made(transport)
        self._delegate_protocol = delegate_protocol

    def connection_lost(self, exc: Optional[Exception]) -> None:
        delegate_protocol = self._delegate_protocol
        if delegate_protocol is not None:
            delegate_protocol.connection_lost(exc)
        self._delegate_protocol = None

    def pause_writing(self) -> None:
        delegate_protocol = self._delegate_protocol
        if delegate_protocol is not None:
            delegate_protocol.pause_writing()

    def resume_writing(self) -> None:
        delegate_protocol = self._delegate_protocol
        if delegate_protocol is not None:
            delegate_protocol.resume_writing()

    def pause_reading(self) -> None:
        delegate_protocol = self._delegate_protocol
        if delegate_protocol is not None:
            delegate_protocol.pause_reading()

    def resume_reading(self) -> None:
        delegate_protocol = self._delegate_protocol
        if delegate_protocol is not None:
            delegate_protocol.resume_reading()

    def get_buffer(self, sizehint: int):
        delegate_protocol = self._delegate_protocol
        if delegate_protocol is not None:
            # pyre-ignore ok, only buffered delegate will have this
            return delegate_protocol.get_buffer(sizehint)

        return bytearray(sizehint)

    def buffer_updated(self, nbytes: int):
        delegate_protocol = self._delegate_protocol
        if delegate_protocol is not None:
            # pyre-ignore ok, only buffered delegate will have this
            delegate_protocol.buffer_updated(nbytes)

    def data_received(self, data: bytes):
        delegate_protocol = self._delegate_protocol
        if delegate_protocol is not None:
            # pyre-ignore ok, only unbuffered delegate will have this
            delegate_protocol.data_received(data)
