import errno
import socket
from abc import abstractmethod, ABCMeta

from bxcommon import constants
from bxcommon.connections.abstract_node import AbstractNode
from bxcommon.constants import LISTEN_ON_IP_ADDRESS
from bxcommon.network.socket_connection import SocketConnection
from bxcommon.network.socket_connection_state import SocketConnectionState
from bxcommon.utils import logger


class AbstractNetworkEventLoop(object):
    __metaclass__ = ABCMeta

    """
    Class is responsible for effective network communication.
    All network related code must be part of this class or its descendants.
    Takes instance of AbstractNode and calls its corresponding methods whenever it is optimal time to
    send, receive, connect or disconnect.
    """

    def __init__(self, node):
        assert isinstance(node, AbstractNode)

        self._node = node
        self._socket_connections = {}
        self._receive_buf = bytearray(constants.RECV_BUFSIZE)

    def run(self):
        """
        Starts event_loop
        """

        logger.debug("Start network event loop")

        try:
            self._start_server()

            self._connect_to_peers()

            timeout = self._node.get_sleep_timeout(triggered_by_timeout=False, first_call=True)

            while True:
                self._process_disconnect_requests()

                if self._node.force_exit():
                    logger.debug("Ending events loop. Shutdown has been requested.")
                    break

                events_count = self._process_events(timeout)

                self._send_all_connections()

                self._process_new_connections_requests()

                timeout = self._node.get_sleep_timeout(events_count == 0)
        finally:
            self.close()

    def close(self):
        """
        Closes node and related resources
        """

        self._node.close()

        for _, socket_connection in self._socket_connections.iteritems():
            socket_connection.close()

    @abstractmethod
    def _process_events(self, timeout):
        pass

    def _start_server(self):

        server_address = self._node.get_server_address()

        listen_port = server_address[1]

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        logger.debug("Creating a server socket on {0}:{1}".format(LISTEN_ON_IP_ADDRESS, listen_port))

        try:
            server_socket.bind((LISTEN_ON_IP_ADDRESS, listen_port))
            server_socket.listen(50)
            server_socket.setblocking(0)

            self._register_socket(server_socket, (LISTEN_ON_IP_ADDRESS, listen_port), is_server=True)

            logger.debug("Finished creating a server socket on {0}:{1}".format(LISTEN_ON_IP_ADDRESS, listen_port))
            return server_socket

        except socket.error as e:
            if e.errno in [errno.EACCES, errno.EADDRINUSE, errno.EADDRNOTAVAIL, errno.ENOMEM, errno.EOPNOTSUPP]:
                logger.fatal("Fatal error: " + str(e.errno) + " " + e.strerror +
                             " Occurred while setting up server socket on {0}:{1}. Exiting..."
                             .format(LISTEN_ON_IP_ADDRESS, listen_port))
                exit(1)
            else:
                logger.fatal("Fatal error: " + str(e.errno) + " " + e.strerror +
                             " Occurred while setting up server socket on {0}:{1}. Re-raising".format(LISTEN_ON_IP_ADDRESS, listen_port))
                raise e

    def _connect_to_peers(self):
        peers_addresses = self._node.get_peers_addresses()

        if peers_addresses:
            for address in peers_addresses:
                self._connect_to_server(address[0], address[1])

    def _process_new_connections_requests(self):
        address = self._node.pop_next_connection_address()

        while address is not None:
            self._connect_to_server(address[0], address[1])
            print "Connected to {0}, {1}".format(address[0], address[1])
            address = self._node.pop_next_connection_address()

    def _process_disconnect_requests(self):
        fileno = self._node.pop_next_disconnect_connection()

        while fileno is not None:
            if fileno in self._socket_connections:
                socket_connection = self._socket_connections[fileno]

                if not socket_connection.state & SocketConnectionState.MARK_FOR_CLOSE:
                    socket_connection.close()
                    self._node.on_connection_closed(fileno)
            fileno = self._node.pop_next_disconnect_connection()

    def _connect_to_server(self, ip, port):
        sock = None

        initialized = True  # True if socket is connected. False otherwise.

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            sock.setblocking(0)
            sock.connect((ip, port))
        except socket.error as e:
            if e.errno in [errno.EPERM, errno.EADDRINUSE]:
                logger.error("Connection to {0}:{1} failed! Got errno {2} with msg {3}."
                             .format(ip, port, e.errno, e.strerror))
                return
            elif e.errno in [errno.EAGAIN, errno.ECONNREFUSED, errno.EINTR, errno.EISCONN, errno.ENETUNREACH,
                             errno.ETIMEDOUT]:
                raise RuntimeError('FIXME')

                # FIXME conn_obj and trusted are not defined, delete trust, alarm register call and test
                # logger.error("Node.connect_to_address",
                #         "Connection to {0}:{1} failed. Got errno {2} with msg {3}. Retry?: {4}"
                #         .format(ip, port, e.errno, e.strerror, conn_obj.trusted))
                # if trusted:
                #     self.alarm_queue.register_alarm(FAST_RETRY, self.retry_init_client_socket, sock, conn_cls, ip,
                #                                     port, setup)
                # return
            elif e.errno in [errno.EALREADY]:
                # Can never happen because this thread is the only one using the socket.
                logger.error("Got EALREADY while connecting to {0}:{1}.".format(ip, port))
                exit(1)
            elif e.errno in [errno.EINPROGRESS]:
                logger.debug("Got EINPROGRESS on {0}:{1}. Will wait for ready outputbuf.".format(ip, port))
                initialized = False
            else:
                raise e

        self._register_socket(sock, (ip, port), is_server=False, initialized=initialized, from_me=True)

    def _handle_incoming_connections(self, socket_connection):
        logger.info("new connection establishment starting")
        try:
            while True:
                new_socket, address = socket_connection.socket_instance.accept()
                logger.debug("new connection from {0}".format(address))

                new_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                new_socket.setblocking(0)

                self._register_socket(new_socket, address, is_server=False, initialized=True, from_me=False)
        except socket.error:
            pass

    def _receive(self, socket_connection):
        assert isinstance(socket_connection, SocketConnection)

        fileno = socket_connection.fileno()

        logger.debug("Collecting input from {0}".format(fileno))
        collect_input = True

        while collect_input:
            # Read from the socket and store it into the receive buffer.
            try:
                bytes_read = socket_connection.socket_instance.recv_into(self._receive_buf, constants.RECV_BUFSIZE)
            except socket.error as e:
                if e.errno in [errno.EAGAIN, errno.EWOULDBLOCK]:
                    logger.debug("Received errno {0} with msg {1} on connection {2}. Stop collecting input"
                                 .format(e.errno, e.strerror, fileno))
                    break
                elif e.errno in [errno.EINTR]:
                    # we were interrupted, try again
                    logger.debug("Received errno {0} with msg {1}, receive on {2} failed. Continuing recv."
                                 .format(e.errno, e.strerror, fileno))
                    continue
                elif e.errno in [errno.ECONNREFUSED]:
                    # Fatal errors for the connections
                    logger.debug("Received errno {0} with msg {1}, receive on {2} failed. "
                                 "Closing connection and retrying..."
                                 .format(e.errno, e.strerror, fileno))
                    socket_connection.set_state(SocketConnectionState.MARK_FOR_CLOSE)
                    return
                elif e.errno in [errno.ECONNRESET, errno.ETIMEDOUT, errno.EBADF]:
                    # Perform orderly shutdown
                    socket_connection.set_state(SocketConnectionState.MARK_FOR_CLOSE)
                    return
                elif e.errno in [errno.EFAULT, errno.EINVAL, errno.ENOTCONN, errno.ENOMEM]:
                    # Should never happen errors
                    logger.error("Received errno {0} with msg {1}, receive on {2} failed. This should never happen..."
                                 .format(e.errno, e.strerror, fileno))
                    return
                else:
                    raise e

            piece = self._receive_buf[:bytes_read]
            logger.debug("Got {0} bytes from {2}. They were: {1}".format(bytes_read, repr(piece), fileno))

            if bytes_read == 0:
                socket_connection.set_state(SocketConnectionState.MARK_FOR_CLOSE)
                self._node.on_connection_closed(fileno)
                return
            else:
                self._node.on_bytes_received(fileno, piece)

    def _send(self, socket_connection):
        assert isinstance(socket_connection, SocketConnection)

        fileno = socket_connection.fileno()

        total_bytes_written = 0
        bytes_written = 0

        # Send on the socket until either the socket is full or we have nothing else to send.
        while socket_connection.can_send and not socket_connection.state & SocketConnectionState.MARK_FOR_CLOSE:
            try:
                send_buffer = self._node.get_bytes_to_send(fileno)

                if not send_buffer:
                    break

                bytes_written = socket_connection.socket_instance.send(send_buffer)
            except socket.error as e:
                if e.errno in [errno.EAGAIN, errno.EWOULDBLOCK, errno.ENOBUFS]:
                    # Normal operation
                    logger.debug("Got {0}. Done sending to {1}. Marking as not sendable."
                                 .format(e.strerror, fileno))
                    socket_connection.can_send = False
                elif e.errno in [errno.EINTR]:
                    # Try again later errors
                    logger.debug("Got {0}. Send to {1} failed, trying again...".format(e.strerror, fileno))
                    continue
                elif e.errno in [errno.EACCES, errno.ECONNRESET, errno.EPIPE, errno.EHOSTUNREACH]:
                    # Fatal errors for the connection
                    logger.debug("Got {0}, send to {1} failed, closing connection.".format(e.strerror, fileno))
                    socket_connection.set_state(SocketConnectionState.MARK_FOR_CLOSE)
                    return 0
                elif e.errno in [errno.ECONNRESET, errno.ETIMEDOUT, errno.EBADF]:
                    # Perform orderly shutdown
                    socket_connection.set_state(SocketConnectionState.MARK_FOR_CLOSE)
                    return 0
                elif e.errno in [errno.EDESTADDRREQ, errno.EFAULT, errno.EINVAL,
                                 errno.EISCONN, errno.EMSGSIZE, errno.ENOTCONN, errno.ENOTSOCK]:
                    # Should never happen errors
                    logger.debug("Got {0}, send to {1} failed. Should not have happened..."
                                 .format(e.strerror, fileno))
                    exit(1)
                elif e.errno in [errno.ENOMEM]:
                    # Fatal errors for the node
                    logger.debug("Got {0}, send to {1} failed. Fatal error! Shutting down node."
                                 .format(e.strerror, fileno))
                    exit(1)
                else:
                    raise e

            total_bytes_written += bytes_written
            self._node.on_bytes_sent(fileno, bytes_written)

            bytes_written = 0

        return total_bytes_written

    def _send_all_connections(self):
        for _, socket_connection in self._socket_connections.iteritems():
            if socket_connection.can_send and not socket_connection.is_server:
                self._send(socket_connection)

    def _register_socket(self, new_socket, address, is_server=False, initialized=True, from_me=False):
        socket_connection = SocketConnection(new_socket, is_server)

        if initialized:
            socket_connection.set_state(SocketConnectionState.INITIALIZED)

        self._socket_connections[new_socket.fileno()] = socket_connection

        if not is_server:
            self._node.on_connection_added(new_socket.fileno(), address[0], address[1], from_me)

            if initialized:
                self._node.on_connection_initialized(new_socket.fileno())
