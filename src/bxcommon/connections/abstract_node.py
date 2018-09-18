import signal
from collections import defaultdict, deque

from bxcommon.connections.connection_pool import ConnectionPool
from bxcommon.connections.connection_state import ConnectionState
from bxcommon.constants import CONNECTION_TIMEOUT, FAST_RETRY, MAX_RETRIES, RETRY_INTERVAL
from bxcommon.exceptions import TerminationError
from bxcommon.services.transaction_service import TransactionService
from bxcommon.utils import logger
from bxcommon.utils.alarm import AlarmQueue


class AbstractNode(object):
    def __init__(self, server_ip, server_port):
        self.connection_queue = deque()
        self.disconnect_queue = deque()

        self.server_ip = server_ip
        self.server_port = server_port

        self.connection_pool = ConnectionPool()
        self.send_pings = False
        self.should_force_exit = False

        self.num_retries_by_ip = defaultdict(lambda: 0)

        # Handle termination gracefully
        signal.signal(signal.SIGTERM, self._kill_node)
        signal.signal(signal.SIGINT, self._kill_node)

        # Event handling queue for delayed events
        self.alarm_queue = AlarmQueue()

        self.tx_service = TransactionService(self)

        logger.info("initialized node state")

    def get_server_address(self):
        return self.server_ip, self.server_port

    def get_peers_addresses(self):
        raise NotImplementedError()

    def on_connection_added(self, fileno, ip, port, from_me):

        # If we're already connected to the remote peer, log the event and request disconnect.
        if self.connection_pool.has_connection(ip, port):
            logger.error("Connection to {0}:{1} already exists!".format(ip, port))
            self.enqueue_disconnect(fileno)
        else:
            self._add_connection(fileno, ip, port, from_me)

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

        self._destroy_conn(conn)

    def on_bytes_received(self, fileno, bytes_received):
        conn = self.connection_pool.get_byfileno(fileno)

        if conn is None:
            logger.warn("Received bytes for connection not in pool. Fileno {0}".format(fileno))
            return

        if conn.state & ConnectionState.MARK_FOR_CLOSE:
            return

        conn.add_received_bytes(bytes_received)

        if conn.state & ConnectionState.MARK_FOR_CLOSE:
            self._destroy_conn(conn, teardown=True)

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
                timeout = 0.1

            return timeout
        else:
            return self.alarm_queue.fire_ready_alarms(triggered_by_timeout)

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
            self._destroy_conn(conn, teardown=True)

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

    def can_retry_after_destroy(self, teardown, conn):
        raise NotImplementedError()

    def get_connection_class(self, ip=None, port=None):
        raise NotImplementedError()

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

    def _add_connection(self, fileno, ip, port, from_me):
        conn_cls = self.get_connection_class(ip=ip, port=port)

        conn_obj = conn_cls(fileno, (ip, port), self, from_me=from_me)

        self.alarm_queue.register_alarm(CONNECTION_TIMEOUT, self._connection_timeout, conn_obj)

        # Make the connection object publicly accessible
        self.connection_pool.add(fileno, ip, port, conn_obj)

        logger.debug("Connected {0}:{1} on file descriptor {2} with state {3}"
                     .format(ip, port, fileno, conn_obj.state))

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
        self._destroy_conn(conn, teardown=True)

        # It is connect_to_address's job to schedule this function.
        return 0

    def _kill_node(self, _signum, _stack):
        """
        Kills the node immediately
        """
        raise TerminationError("Node killed.")

    def _destroy_conn(self, conn, teardown=False):
        """
        Clean up the associated connection and update all data structures tracking it.
        We also retry trusted connections since they can never be destroyed.
        If teardown is True, then we do not retry trusted connections and just tear everything down.
        """

        logger.debug("Breaking connection to {0}".format(conn.peer_desc))

        self.connection_pool.delete(conn)
        conn.close()

        if teardown:
            self.enqueue_disconnect(conn.fileno)

        if teardown and self.can_retry_after_destroy(teardown, conn):
            logger.debug("Retrying connection to {0}".format(conn.peer_desc))
            self.alarm_queue.register_alarm(FAST_RETRY, self._retry_init_client_socket, conn.peer_ip, conn.peer_port)

        if not teardown and conn.is_persistent:
            self.alarm_queue.register_alarm(RETRY_INTERVAL, self._retry_init_client_socket, conn.peer_ip,
                                            conn.peer_port)

    def _retry_init_client_socket(self, ip, port):
        self.num_retries_by_ip[ip] += 1
        if self.num_retries_by_ip[ip] >= MAX_RETRIES:
            del self.num_retries_by_ip[ip]
            logger.debug("Not retrying connection to {0}:{1}- maximum connections exceeded!".format(ip, port))
            return 0
        else:
            logger.debug("Retrying connection to {0}:{1}.".format(ip, port))
            self.enqueue_connection(ip, port)
        return 0
