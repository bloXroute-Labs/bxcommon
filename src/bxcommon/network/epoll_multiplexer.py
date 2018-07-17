import errno
import select

from bxcommon.network.abstract_multiplexer import AbstractMultiplexer
from bxcommon.network.socket_connection import SocketConnection
from bxcommon.network.socket_connection_state import SocketConnectionState
from bxcommon.utils import logger


class EpollMultiplexer(AbstractMultiplexer):
    def __init__(self):

        self._epoll = select.epoll()

    def run(self):
        try:
            timeout = self._communication_strategy.get_next_sleep_timeout()

            while True:
                # Grab all events.
                try:
                    if timeout is None:
                        timeout = -1

                    events = self._epoll.poll(timeout)
                except IOError as ioe:
                    if ioe.errno == errno.EINTR:
                        logger.info("got interrupted in epoll")
                        continue
                    raise ioe

                for fileno, event in events:

                    if fileno in self._socket_connections:
                        socket_connection = self._socket_connections[fileno]
                        assert isinstance(socket_connection, SocketConnection)

                        # Mark this connection for close if we received a POLLHUP. No other functions will be called
                        #   on this connection.
                        if event & select.EPOLLHUP:
                            socket_connection.state.set_state(SocketConnectionState.MARK_FOR_CLOSE)
                            self._communication_strategy.remove_connection(fileno)

                        if event & select.EPOLLOUT and not socket_connection.state & SocketConnectionState.MARK_FOR_CLOSE:
                            # If connect received EINPROGRESS, we will receive an EPOLLOUT if connect succeeded
                            if not socket_connection.state & SocketConnectionState.INITIALIZED:
                                socket_connection.state = socket_connection.state | SocketConnectionState.INITIALIZED

                            # Mark the connection as sendable and send as much as we can from the outputbuffer.
                            socket_connection.can_send = True

                            self._send(socket_connection)

                    # handle incoming connection on the server port
                    elif socket_connection.is_server:
                        self._handle_incoming_connections(socket_connection)

                    else:
                        assert False, "Connection not handled!"

                # Handle EPOLLIN events.
                for fileno, event in events:

                    socket_connection = self._socket_connections[fileno]
                    assert isinstance(socket_connection, SocketConnection)

                    # we already handled the new connections above, no need to handle them again
                    if not socket_connection.is_server:

                        if event & select.EPOLLIN and not socket_connection.state & SocketConnectionState.MARK_FOR_CLOSE:
                            self._receive(socket_connection)

                        # Done processing. Close socket if it got put on the blacklist or was marked for close.
                        if socket_connection.state & SocketConnectionState.MARK_FOR_CLOSE:
                            logger.debug("Connection to {0} closing".format(socket_connection.id()))
                            socket_connection.close()
                            self._communication_strategy.remove_connection(fileno)

                timeout = self._communication_strategy.get_next_sleep_timeout()
        finally:
            self.close()

    def close(self):
        super(EpollMultiplexer, self).close()

        self._epoll.close()

    def _register_socket(self, new_socket, is_server=False, initialized=True):
        super(EpollMultiplexer, self)._register_socket(new_socket, is_server)

        if is_server:
            self._epoll.register(new_socket.fileno(), select.EPOLLIN | select.EPOLLET)
        else:
            self._epoll.register(new_socket.fileno(),
                                 select.EPOLLOUT | select.EPOLLIN | select.EPOLLERR | select.EPOLLHUP | select.EPOLLET)
