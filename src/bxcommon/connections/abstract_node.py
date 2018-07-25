import signal
from collections import defaultdict

from bxcommon.connections.connection_pool import ConnectionPool
from bxcommon.connections.connection_state import ConnectionState
from bxcommon.exceptions import TerminationError
from bxcommon.network.abstract_communication_strategy import AbstractCommunicationStrategy
from bxcommon.services.transaction_service import TransactionService
from bxcommon.utils import logger
from bxcommon.utils.alarm import AlarmQueue


class AbstractNode(AbstractCommunicationStrategy):
    def __init__(self, server_ip, server_port):
        super(AbstractNode, self).__init__()

        self.server_ip = server_ip
        self.server_port = server_port

        self.connection_pool = ConnectionPool()
        self.send_pings = False

        self.num_retries_by_ip = defaultdict(lambda: 0)

        # Handle termination gracefully
        signal.signal(signal.SIGTERM, self._kill_node)
        signal.signal(signal.SIGINT, self._kill_node)

        # Event handling queue for delayed events
        self.alarm_queue = AlarmQueue()

        self.tx_service = TransactionService(self)

        logger.info("initialized node state")

    # Begin AbstractCommunicationStrategy implementation

    def get_server_address(self):
        return (self.server_ip, self.server_port)
    
    def get_peers_addresses(self):
        raise NotImplementedError()

    def on_connection_added(self, connection_id, ip, port, from_me):
        self._add_connection(connection_id, ip, port, from_me)

    def on_connection_closed(self, connection_id):
        self._destroy_conn(connection_id)

    def on_bytes_received(self, connection_id, bytes_received):
        conn = self.connection_pool.get_byfileno(connection_id)

        if conn is None:
            logger.warn("Received bytes for connection not in pool. Connection id {0}".format(connection_id))
            return

        conn.add_received_bytes(bytes_received)

    def get_bytes_to_send(self, connection_id):
        conn = self.connection_pool.get_byfileno(connection_id)

        if conn is None:
            logger.warn("Request to get bytes for connection not in pool. Connection id {0}".format(connection_id))
            return None

        return conn.get_bytes_to_send()

    def on_bytes_sent(self, connection_id, bytes_sent):
        conn = self.connection_pool.get_byfileno(connection_id)

        if conn is None:
            logger.warn("Bytes sent call for connection not in pool. Connection id {0}".format(connection_id))
            return None

        return conn.advance_sent_bytes(bytes_sent)

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
        pass

    def close(self):
        logger.error("Node is closing! Closing everything.")

        for conn in self.connection_pool:
            self._destroy_conn(conn.fileno, teardown=True)

    # End AbstractCommunicationStrategy implementation

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

    def _add_connection(self, connection_id, ip, port, from_me):
        conn_cls = self.get_connection_class(ip=ip, port=port)

        conn_obj = conn_cls(connection_id, (ip, port), self, from_me=from_me)

        # Make the connection object publicly accessible
        self.connection_pool.add(connection_id, ip, port, conn_obj)

        logger.debug("Connected {0}:{1} on file descriptor {2} with state {3}"
                     .format(ip, port, connection_id, conn_obj.state))

    def _kill_node(self, _signum, _stack):
        """
        Kills the node immediately
        """
        raise TerminationError("Node killed.")

    def _destroy_conn(self, fileno, teardown=False):
        """
        Clean up the associated connection and update all data structures tracking it.
        We also retry trusted connections since they can never be destroyed.
        If teardown is True, then we do not retry trusted connections and just tear everything down.
        """

        logger.debug("Breaking connection to {0}".format(fileno))
        conn = self.connection_pool.get_byfileno(fileno)

        if conn is not None:
            self.connection_pool.delete(conn)
            conn.close()
