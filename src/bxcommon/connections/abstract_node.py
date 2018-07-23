import heapq
import signal

from collections import defaultdict

from bxcommon.connections.connection_pool import ConnectionPool
from bxcommon.connections.connection_state import ConnectionState
from bxcommon.constants import CONNECTION_TIMEOUT, FAST_RETRY, MAX_RETRIES, RETRY_INTERVAL
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
        signal.signal(signal.SIGTERM, self.kill_node)
        signal.signal(signal.SIGINT, self.kill_node)

        # Event handling queue for delayed events
        self.alarm_queue = AlarmQueue()

        self.tx_service = TransactionService(self)

        logger.info("initialized node state")

    # Begin AbstractCommunicationStrategy methods override

    def get_server_address(self):
        return (self.server_ip, self.server_port)

    def on_connection_added(self, connection_id, ip, port, from_me):
        self.add_connection(connection_id, ip, port, from_me)

    def on_connection_closed(self, connection_id):
        self.destroy_conn(connection_id)

    def on_receive(self, connection_id, bytes_received):
        # TODO: Call connection method here
        pass

    def on_send(self, connection_id):
        # TODO: Call connection method here
        pass

    def on_sent(self, connection_id, bytes_sent):
        # TODO: Call connection method here
        pass

    def on_first_sleep(self):
        _, timeout = self.alarm_queue.time_to_next_alarm()
        return timeout

    def on_sleep(self, triggered_by_timeout):
        return self.alarm_queue.fire_ready_alarms(triggered_by_timeout)

    def on_chance_to_exit(self):
        pass

    def on_close(self):
        logger.error("Node is closing! Closing everything.")

        for conn in self.connection_pool:
            self.destroy_conn(conn.fileno, teardown=True)

    # End AbstractCommunicationStrategy methods override

    def add_connection(self, connection_id, ip, port, from_me):
        conn_cls = self.get_connection_class()

        conn_obj = conn_cls((ip, port), self, from_me=from_me)

        # Make the connection object publicly accessible
        self.connection_pool.add(connection_id, ip, port, conn_obj)
        logger.debug("Connected {0}:{1} on file descriptor {2} with state {3}"
                     .format(ip, port, connection_id, conn_obj.state))

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

    def kill_node(self, _signum, _stack):
        """
        Kills the node immediately
        """
        raise TerminationError("Node killed.")

    def destroy_conn(self, fileno, teardown=False):
        """
        Clean up the associated connection and update all data structures tracking it.
        We also retry trusted connections since they can never be destroyed.
        If teardown is True, then we do not retry trusted connections and just tear everything down.
        """

        conn = self.connection_pool.get_byfileno(fileno)
        logger.debug("Breaking connection to {0}".format(conn.peer_desc))

        self.connection_pool.delete(conn)

        conn.on_close()

    def can_retry_after_destroy(self, teardown, conn):
        raise NotImplementedError()

    def get_connection_class(self, ip=None):
        raise NotImplementedError()

    def configure_peers(self):
        raise NotImplementedError()
