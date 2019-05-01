import errno
import socket
from abc import ABCMeta, abstractmethod

from bxcommon.connections.abstract_node import AbstractNode
from bxcommon.constants import LISTEN_ON_IP_ADDRESS
from bxcommon.network.socket_connection import SocketConnection
from bxcommon.network.transport_layer_protocol import TransportLayerProtocol
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

    def run(self):
        """
        Starts event_loop
        """

        logger.debug("Start network event loop...")

        try:
            self._start_server()

            self._connect_to_sdn()

            self._connect_to_peers()

            timeout = self._node.get_sleep_timeout(triggered_by_timeout=False, first_call=True)

            while True:
                events_count = self._process_events(timeout)

                self._process_disconnect_requests()

                if self._node.force_exit():
                    logger.info("Ending event loop. Shutdown has been requested.")
                    break

                self._node.flush_all_send_buffers()

                self._process_new_connections_requests()

                timeout = self._node.get_sleep_timeout(events_count == 0)
        finally:
            self.close()

    def close(self):
        """
        Closes node and related resources
        """

        self._node.close()

        for _, socket_connection in self._socket_connections.items():
            socket_connection.close()

    @abstractmethod
    def _process_events(self, timeout):
        pass

    def _start_server(self):

        external_port = self._node.opts.external_port

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        logger.info("Creating a server socket on {0}:{1}...".format(LISTEN_ON_IP_ADDRESS, external_port))

        try:
            server_socket.bind((LISTEN_ON_IP_ADDRESS, external_port))
            server_socket.listen(50)
            server_socket.setblocking(False)

            self._register_socket(server_socket, (LISTEN_ON_IP_ADDRESS, external_port), is_server=True)

            logger.info("Server socket creation successful.")
            return server_socket

        except socket.error as e:
            if e.errno in [errno.EACCES, errno.EADDRINUSE, errno.EADDRNOTAVAIL, errno.ENOMEM, errno.EOPNOTSUPP]:
                logger.fatal("Fatal error: " + str(e.errno) + " " + e.strerror +
                             " Occurred while setting up server socket on {0}:{1}. Exiting..."
                             .format(LISTEN_ON_IP_ADDRESS, external_port))
                exit(1)
            else:
                logger.fatal("Fatal error: " + str(e.errno) + " " + e.strerror +
                             " Occurred while setting up server socket on {0}:{1}. Re-raising".format(
                                 LISTEN_ON_IP_ADDRESS,
                                 external_port))
                raise e

    def _connect_to_sdn(self):
        sdn_address = self._node.get_sdn_address()

        if sdn_address:
            self._connect_to_server(sdn_address[0], sdn_address[1])
        else:
            logger.warn("SDN address not provided, skipping connection. This is expected for gateways.")

    def _connect_to_peers(self):
        peers_addresses = self._node.get_outbound_peer_addresses()

        if peers_addresses:
            for address in peers_addresses:
                protocol = address[2] if len(address) == 3 else None
                logger.info("Connecting to node {0}:{1} on protocol: {2}.".format(address[0], address[1], protocol))

                self._connect_to_server(address[0], address[1], protocol)

    def _process_new_connections_requests(self):
        address = self._node.pop_next_connection_address()

        while address is not None:
            self._connect_to_server(address[0], address[1])
            address = self._node.pop_next_connection_address()

    def _process_disconnect_requests(self):
        fileno = self._node.pop_next_disconnect_connection()

        while fileno is not None:
            if fileno in self._socket_connections:
                logger.debug("Closing connection to {0}".format(fileno))
                socket_connection = self._socket_connections[fileno]
                socket_connection.close()

                # TODO this line should be removed as well. The network layer should not be telling
                # the node when a connection is closed.
                self._node.on_connection_closed(fileno)

                # TODO: This if statement should be removed (i.e. MARK_FOR_CLOSE should be set more carefully)
                if not socket_connection.state & SocketConnectionState.MARK_FOR_CLOSE:
                    logger.error("Connection on fileno {0} was enqueued for disconnect without being marked for close!".format(fileno))
            else:
                logger.warn("Fileno {0} could not be closed".format(fileno))

            fileno = self._node.pop_next_disconnect_connection()

    def _connect_to_server(self, ip, port, protocol=TransportLayerProtocol.TCP):
        if self._node.connection_exists(ip, port):
            logger.warn("Ignoring repeat connection to {0}:{1}.".format(ip, port))
            return

        sock = None

        initialized = True  # True if socket is connected. False otherwise.

        try:
            socket_stream = socket.SOCK_DGRAM if protocol == TransportLayerProtocol.UDP else socket.SOCK_STREAM

            sock = socket.socket(socket.AF_INET, socket_stream)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

            if protocol == TransportLayerProtocol.TCP:
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            sock.setblocking(False)
            sock.connect((ip, port))
        except socket.error as e:
            if e.errno in [errno.EPERM, errno.EADDRINUSE]:
                logger.error("Connection to {0}:{1} failed! Got errno {2} with msg {3}."
                             .format(ip, port, e.errno, e.strerror))
                return
            elif e.errno in [errno.EAGAIN, errno.ECONNREFUSED, errno.EINTR, errno.EISCONN, errno.ENETUNREACH,
                             errno.ETIMEDOUT]:
                logger.error("Connection to {0}:{1} failed. Got errno {2} with msg {3}"
                             .format(ip, port, e.errno, e.strerror))
                return
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
        logger.info("Connected to {0}:{1}.".format(ip, port))

    def _handle_incoming_connections(self, socket_connection):
        logger.info("Received incoming request(s) for connection...")
        try:
            while True:
                new_socket, address = socket_connection.socket_instance.accept()
                logger.info("Accepted new connection from {0}.".format(address))

                new_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                new_socket.setblocking(0)

                self._register_socket(new_socket, address, is_server=False, initialized=True, from_me=False)
        except socket.error:
            pass

    def _register_socket(self, new_socket, address, is_server=False, initialized=True, from_me=False):
        socket_connection = SocketConnection(new_socket, self._node, is_server)

        if initialized:
            socket_connection.set_state(SocketConnectionState.INITIALIZED)

        self._socket_connections[new_socket.fileno()] = socket_connection

        if not is_server:
            self._node.on_connection_added(socket_connection, address[0], address[1], from_me)

            if initialized:
                self._node.on_connection_initialized(new_socket.fileno())
