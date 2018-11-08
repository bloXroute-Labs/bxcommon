import errno
import select

from bxcommon.network.abstract_network_event_loop import AbstractNetworkEventLoop
from bxcommon.network.socket_connection import SocketConnection
from bxcommon.network.socket_connection_state import SocketConnectionState
from bxcommon.utils import logger


class EpollNetworkEventLoop(AbstractNetworkEventLoop):
    def __init__(self, node):
        super(EpollNetworkEventLoop, self).__init__(node)
        self._epoll = select.epoll()

    def close(self):
        super(EpollNetworkEventLoop, self).close()

        self._epoll.close()

    def _process_events(self, timeout):
        if timeout is None:
            timeout = -1

        # Grab all events.
        try:
            events = self._epoll.poll(timeout)
        except IOError as ioe:
            if ioe.errno == errno.EINTR:
                logger.info("got interrupted in epoll")
                return 0
            raise ioe

        receive_connections = []

        for fileno, event in events:

            if fileno in self._socket_connections:
                socket_connection = self._socket_connections[fileno]
                assert isinstance(socket_connection, SocketConnection)

                if socket_connection.is_server:
                    self._handle_incoming_connections(socket_connection)
                else:
                    # Mark this connection for close if we received a POLLHUP. No other functions will be called
                    #   on this connection.
                    if event & select.EPOLLHUP:
                        socket_connection.set_state(SocketConnectionState.MARK_FOR_CLOSE)
                        self._node.on_connection_closed(fileno)

                    if event & select.EPOLLOUT and \
                            not socket_connection.state & SocketConnectionState.MARK_FOR_CLOSE:
                        # If connect received EINPROGRESS, we will receive an EPOLLOUT if connect succeeded
                        if not socket_connection.state & SocketConnectionState.INITIALIZED:
                            socket_connection.set_state(SocketConnectionState.INITIALIZED)
                            self._node.on_connection_initialized(fileno)

                        # Mark the connection as sendable and send as much as we can from the outputbuffer.
                        socket_connection.can_send = True

                        socket_connection.send()

                    if event & select.EPOLLIN and \
                            not socket_connection.state & SocketConnectionState.MARK_FOR_CLOSE:
                        receive_connections.append(socket_connection)
            else:
                assert False, "Connection not handled!"

        # Process receive events in the end
        for socket_connection in receive_connections:
            socket_connection.receive()

        return len(events)

    def _register_socket(self, new_socket, address, is_server=False, initialized=True, from_me=False):
        super(EpollNetworkEventLoop, self)._register_socket(new_socket, address, is_server, initialized, from_me)

        if is_server:
            self._epoll.register(new_socket.fileno(), select.EPOLLIN | select.EPOLLET)
        else:
            self._epoll.register(new_socket.fileno(),
                                 select.EPOLLOUT | select.EPOLLIN | select.EPOLLERR | select.EPOLLHUP | select.EPOLLET)
