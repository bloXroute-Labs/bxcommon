import errno
import select
import socket
from typing import Tuple

from bxcommon.network.abstract_network_event_loop import AbstractNetworkEventLoop
from bxcommon.network.socket_connection_state import SocketConnectionState
from bxutils import logging

logger = logging.get_logger(__name__)


class EpollNetworkEventLoop(AbstractNetworkEventLoop):
    """
    Implementation of network event loop for Linux that uses epoll

    Documentation for 'select' and 'epoll' - https://docs.python.org/2/library/select.html
    """

    def __init__(self, node):
        super(EpollNetworkEventLoop, self).__init__(node)
        self._epoll = select.epoll()

    def close(self):
        super(EpollNetworkEventLoop, self).close()

        self._epoll.close()

    def _process_events(self, timeout: float) -> int:
        # Grab all events.
        try:
            events = self._epoll.poll(timeout)
        except IOError as ioe:
            if ioe.errno == errno.EINTR:
                logger.debug("epoll was interrupted. Skipping to next iteration of event loop.")
                return 0
            raise ioe

        receive_connections = []

        for fileno, event in events:

            assert fileno in self._socket_connections

            socket_connection = self._socket_connections[fileno]

            if socket_connection.is_server:
                self._handle_incoming_connections(socket_connection)
            else:
                # Mark this connection for close if we received a POLLHUP. No other functions will be called
                # on this connection.
                if event & select.EPOLLHUP:
                    logger.info(
                        "Received close from fileno: {}. Closing connection.", fileno,
                    )
                    socket_connection.mark_for_close()

                if event & select.EPOLLOUT:
                    self._send_on_socket(socket_connection)

                if event & select.EPOLLIN:
                    receive_connections.append(socket_connection)

        # Process receive events in the end
        for socket_connection in receive_connections:
            if not socket_connection.state & SocketConnectionState.MARK_FOR_CLOSE:
                if self._node.on_input_received(socket_connection.fileno()):
                    socket_connection.receive()

        return len(events)

    def _register_socket(
        self,
        new_socket: socket.socket,
        address: Tuple[str, int],
        is_server: bool = False,
        initialized: bool = True,
        from_me: bool = False,
    ):

        super(EpollNetworkEventLoop, self)._register_socket(new_socket, address, is_server, initialized, from_me)

        if is_server:
            self._epoll.register(new_socket.fileno(), select.EPOLLIN | select.EPOLLET)
        else:
            self._epoll.register(
                new_socket.fileno(),
                select.EPOLLOUT | select.EPOLLIN | select.EPOLLERR | select.EPOLLHUP | select.EPOLLET,
            )
