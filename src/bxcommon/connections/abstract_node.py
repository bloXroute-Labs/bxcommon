import signal
from abc import ABCMeta, abstractmethod
from collections import defaultdict, deque

from bxcommon.connections.connection_pool import ConnectionPool
from bxcommon.connections.connection_state import ConnectionState
from bxcommon.constants import CONNECTION_RETRY_SECONDS, CONNECTION_TIMEOUT, DEFAULT_SLEEP_TIMEOUT, MAX_CONNECT_RETRIES, \
    RETRY_BLOCKCHAIN_CONNECT_FOREVER, THROUGHPUT_STATS_INTERVAL
from bxcommon.exceptions import TerminationError
from bxcommon.models.outbound_peer_model import OutboundPeerModel
from bxcommon.network.socket_connection import SocketConnection
from bxcommon.services import sdn_service
from bxcommon.services.transaction_service import TransactionService
from bxcommon.utils import logger
from bxcommon.utils.alarm import AlarmQueue
from bxcommon.utils.throughput.throughput_service import throughput_service


class AbstractNode(object):
    __meta__ = ABCMeta
    node_type = None

    def __init__(self, opts):
        logger.info("Initializing node of type {}".format(self.node_type))

        self.opts = opts

        self.connection_queue = deque()
        self.disconnect_queue = deque()

        self.connection_pool = ConnectionPool()
        self.send_pings = False
        self.should_force_exit = False

        self.num_retries_by_ip = defaultdict(int)

        # Handle termination gracefully
        signal.signal(signal.SIGTERM, self._kill_node)
        signal.signal(signal.SIGINT, self._kill_node)

        # Event handling queue for delayed events
        self.alarm_queue = AlarmQueue()

        self.tx_service = TransactionService(self)

        self.init_throughput_logging()

        logger.info("initialized node state")

    @abstractmethod
    def get_outbound_peer_addresses(self):
        pass

    def connection_exists(self, ip, port):
        return self.connection_pool.has_connection(ip, port)

    def on_connection_added(self, socket_connection, ip, port, from_me):

        if not isinstance(socket_connection, SocketConnection):
            raise ValueError('Type SocketConnection is expected for socket_connection argument but was {0}'
                             .format(socket_connection))

        fileno = socket_connection.fileno()

        # If we're already connected to the remote peer, log the event and request disconnect.
        if self.connection_exists(ip, port):
            logger.error("Connection to {0}:{1} already exists!".format(ip, port))

            # Schedule dropping the added connection and keep the old one.
            self.enqueue_disconnect(fileno)
        else:
            self._add_connection(socket_connection, ip, port, from_me)

    def on_connection_initialized(self, fileno):
        conn = self.connection_pool.get_byfileno(fileno)

        if conn is None:
            logger.warn("Initialized connection not in pool. Fileno {0}".format(fileno))
            return None

        logger.debug("Connection {0} has been initialized.".format(conn.peer_desc))
        conn.state |= ConnectionState.INITIALIZED

    def on_connection_closed(self, fileno):
        conn = self.connection_pool.get_byfileno(fileno)

        if conn is None:
            logger.warn("Closed connection not in pool. Fileno {0}".format(fileno))
            return None

        self._destroy_conn(conn, retry_connection=True)

    def fetch_updated_outbound_peers(self):
        outbound_peers = sdn_service.fetch_outbound_peers(self.opts.node_id)

        # Connect to peers not in our known pool
        peer_set = set()
        for peer in outbound_peers:
            peer_ip = peer.get(OutboundPeerModel.ip)
            peer_port = peer.get(OutboundPeerModel.port)
            peer_set.add((peer_ip, peer_port))
            if not self.connection_pool.has_connection(peer_ip, peer_port):
                self.enqueue_connection(peer_ip, peer_port)

    def on_bytes_received(self, fileno, bytes_received):
        conn = self.connection_pool.get_byfileno(fileno)

        if conn is None:
            logger.warn("Received bytes for connection not in pool. Fileno {0}".format(fileno))
            return

        if conn.state & ConnectionState.MARK_FOR_CLOSE:
            return

        conn.add_received_bytes(bytes_received)

        if conn.state & ConnectionState.MARK_FOR_CLOSE:
            self._destroy_conn(conn)

    def on_finished_receiving(self, fileno):
        conn = self.connection_pool.get_byfileno(fileno)

        if conn is None:
            logger.warn("Received bytes for connection not in pool. Fileno {0}".format(fileno))
            return

        if conn.state & ConnectionState.MARK_FOR_CLOSE:
            return

        conn.process_message()

    def get_bytes_to_send(self, fileno):
        conn = self.connection_pool.get_byfileno(fileno)

        if conn is None:
            logger.warn("Request to get bytes for connection not in pool. Fileno {0}".format(fileno))
            return None

        if conn.state & ConnectionState.MARK_FOR_CLOSE:
            return None

        return conn.get_bytes_to_send()

    def on_bytes_sent(self, fileno, bytes_sent):
        conn = self.connection_pool.get_byfileno(fileno)

        if conn is None:
            logger.warn("Bytes sent call for connection not in pool. Fileno {0}".format(fileno))
            return None

        conn.advance_sent_bytes(bytes_sent)

    def get_sleep_timeout(self, triggered_by_timeout, first_call=False):
        if first_call:
            _, timeout = self.alarm_queue.time_to_next_alarm()

            # Time out can be negative during debugging
            if timeout < 0:
                timeout = DEFAULT_SLEEP_TIMEOUT

            return timeout
        else:
            time_to_next = self.alarm_queue.fire_ready_alarms(triggered_by_timeout)
            if self.connection_queue or self.disconnect_queue:
                time_to_next = DEFAULT_SLEEP_TIMEOUT

            return time_to_next

    def force_exit(self):
        """
        Indicates if node should trigger exit in event loop. Primarily used for testing.

        Typically requires one additional socket call (e.g. connecting to this node via a socket)
        to finish terminating the event loop.
        """
        return self.should_force_exit

    def close(self):
        logger.error("Node is closing! Closing everything.")

        for conn in self.connection_pool:
            self._destroy_conn(conn)

    def broadcast(self, msg, broadcasting_conn):
        """
        Broadcasts message msg to every connection except requester.
        """

        if broadcasting_conn is not None:
            logger.debug("Broadcasting message to everyone from {0}".format(broadcasting_conn.peer_desc))
        else:
            logger.debug("Broadcasting message to everyone")

        for conn in self.connection_pool:
            if conn.state & ConnectionState.ESTABLISHED and conn != broadcasting_conn:
                conn.enqueue_msg(msg)

    @abstractmethod
    def get_connection_class(self, ip=None, port=None):
        pass

    def enqueue_connection(self, ip, port):
        """
        Add address to the queue of outbound connections
        """

        self.connection_queue.append((ip, port))

    def enqueue_disconnect(self, fileno):
        """
        Add address to the queue of connections to disconnect
        """
        self.disconnect_queue.append(fileno)

    def pop_next_connection_address(self):
        """
        Get next address from the queue of outbound connections

        :return: tuple (ip, port)
        """

        if self.connection_queue:
            return self.connection_queue.popleft()

        return None

    def pop_next_disconnect_connection(self):
        """
        Get next Fileno from the queue of disconnect connections

        :return: tuple (ip, port)
        """

        if self.disconnect_queue:
            return self.disconnect_queue.popleft()

        return None

    def _add_connection(self, socket_connection, ip, port, from_me):
        conn_cls = self.get_connection_class(ip=ip, port=port)

        conn_obj = conn_cls(socket_connection, (ip, port), self, from_me=from_me)

        self.alarm_queue.register_alarm(CONNECTION_TIMEOUT, self._connection_timeout, conn_obj)

        # Make the connection object publicly accessible
        self.connection_pool.add(socket_connection.fileno(), ip, port, conn_obj)

        logger.debug("Connected {0}:{1} on file descriptor {2} with state {3}"
                     .format(ip, port, socket_connection.fileno(), conn_obj.state))

    def _connection_timeout(self, conn):
        """
        Check if the connection is established.
        If it is not established, we give up for untrusted connections and try again for trusted connections.
        """

        logger.debug("Connection timeout, on connection with {0}".format(conn.peer_desc))

        if conn.state & ConnectionState.ESTABLISHED:
            logger.debug("Turns out connection was initialized, carrying on with {0}".format(conn.peer_desc))

            if self.send_pings:
                self.alarm_queue.register_alarm(60, conn.send_ping)

            return 0

        if conn.state & ConnectionState.MARK_FOR_CLOSE:
            logger.debug("We're already closing the connection to {0} (or have closed it). Ignoring timeout."
                         .format(conn.peer_desc))
            return 0

        # Clean up the old connection and retry it if it is trusted
        logger.debug("destroying old socket with {0}".format(conn.peer_desc))
        self._destroy_conn(conn, retry_connection=True)

        # It is connect_to_address's job to schedule this function.
        return 0

    def _kill_node(self, _signum, _stack):
        """
        Kills the node immediately
        """
        raise TerminationError("Node killed.")

    def _destroy_conn(self, conn, retry_connection=False):
        """
        Clean up the associated connection and update all data structures tracking it.
        We also retry trusted connections since they can never be destroyed.
        If teardown is True, then we do not retry trusted connections and just tear everything down.
        """

        logger.debug("Breaking connection to {0}".format(conn.peer_desc))

        self.connection_pool.delete(conn)
        conn.mark_for_close()

        if retry_connection:
            peer_ip = conn.peer_ip
            peer_port = conn.peer_port
            if self.is_outbound_peer(peer_ip, peer_port) or self.is_blockchain_node_address(peer_ip, peer_port):
                self.alarm_queue.register_alarm(CONNECTION_RETRY_SECONDS, self._retry_init_client_socket, peer_ip,
                                                peer_port)

        self.enqueue_disconnect(conn.fileno)

    @abstractmethod
    def is_blockchain_node_address(self, ip, port):
        pass

    def is_outbound_peer(self, ip, port):
        if not self.opts.outbound_peers:
            return False

        for peer in self.opts.outbound_peers:
            if ip == peer.get(OutboundPeerModel.ip) and port == peer.get(OutboundPeerModel.port):
                return True

        return False

    def _retry_init_client_socket(self, ip, port):
        self.num_retries_by_ip[ip] += 1

        is_blockchain_node = self.is_blockchain_node_address(ip, port)
        always_retry_blockchain = is_blockchain_node and RETRY_BLOCKCHAIN_CONNECT_FOREVER

        if always_retry_blockchain or self.num_retries_by_ip[ip] < MAX_CONNECT_RETRIES:
            logger.debug("Retrying connection to {0}:{1}.".format(ip, port))
            self.enqueue_connection(ip, port)
        else:
            del self.num_retries_by_ip[ip]
            logger.debug("Not retrying connection to {0}:{1}- maximum connections exceeded!".format(ip, port))

            if not is_blockchain_node:
                sdn_service.submit_peer_connection_error_event(self.opts.node_id, ip, port)
                self.fetch_updated_outbound_peers()

        return 0

    def init_throughput_logging(self):
        self.alarm_queue.register_alarm(THROUGHPUT_STATS_INTERVAL, throughput_service.flush_stats)
