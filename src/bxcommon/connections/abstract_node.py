import os
import signal
from abc import ABCMeta, abstractmethod
from argparse import Namespace
from collections import defaultdict, deque
from typing import List, Optional, Tuple, Dict, Deque, NamedTuple

from bxcommon import constants
from bxcommon.connections.abstract_connection import AbstractConnection
from bxcommon.connections.connection_pool import ConnectionPool
from bxcommon.connections.connection_state import ConnectionState
from bxcommon.connections.connection_type import ConnectionType
from bxcommon.exceptions import TerminationError
from bxcommon.messages.abstract_message import AbstractMessage
from bxcommon.models.blockchain_network_model import BlockchainNetworkModel
from bxcommon.network.socket_connection import SocketConnection
from bxcommon.network.socket_connection_state import SocketConnectionState
from bxcommon.services import sdn_http_service
from bxcommon.services.broadcast_service import BroadcastService, BroadcastOptions
from bxcommon.utils import memory_utils, json_utils
from bxcommon.utils.alarm_queue import AlarmQueue
from bxcommon.utils.stats.block_statistics_service import block_stats
from bxcommon.utils.stats.memory_statistics_service import memory_statistics
from bxcommon.utils.stats.node_info_service import node_info_statistics
from bxcommon.utils.stats.throughput_service import throughput_statistics
from bxcommon.utils.stats.transaction_statistics_service import tx_stats
from bxutils import logging
from bxutils.logging import LogRecordType

logger = logging.get_logger(__name__)
memory_logger = logging.get_logger(LogRecordType.BxMemory)


class DisconnectRequest(NamedTuple):
    fileno: int
    should_retry: bool


class AbstractNode:
    __meta__ = ABCMeta
    FLUSH_SEND_BUFFERS_INTERVAL = constants.OUTPUT_BUFFER_BATCH_MAX_HOLD_TIME * 2
    NODE_TYPE = None

    def __init__(self, opts: Namespace):
        logger.debug("Initializing node of type: {}", self.NODE_TYPE)

        self.set_node_config_opts_from_sdn(opts)
        self.opts = opts
        self.connection_queue: Deque[Tuple[str, int]] = deque()
        self.outbound_peers = opts.outbound_peers[:]

        self.connection_pool = ConnectionPool()
        self.should_force_exit = False

        self.num_retries_by_ip: Dict[Tuple[str, int], int] = defaultdict(int)

        # Handle termination gracefully
        signal.signal(signal.SIGTERM, self._kill_node)
        signal.signal(signal.SIGINT, self._kill_node)
        signal.signal(signal.SIGSEGV, self._kill_node)

        # Event handling queue for delayed events
        self.alarm_queue = AlarmQueue()

        self.init_throughput_logging()
        self.init_node_info_logging()
        self.init_memory_stats_logging()
        self.init_block_stats_logging()
        self.init_tx_stats_logging()

        # TODO: clean this up alongside outputbuffer holding time
        # this is Nagle's algorithm and we need to implement it properly
        # flush buffers regularly because of output buffer holding time
        self.alarm_queue.register_approx_alarm(self.FLUSH_SEND_BUFFERS_INTERVAL,
                                               constants.OUTPUT_BUFFER_BATCH_MAX_HOLD_TIME,
                                               self.flush_all_send_buffers)

        self.network_num = opts.blockchain_network_num
        self.broadcast_service = self.get_broadcast_service()

        # converting setting in MB to bytes
        self.next_report_mem_usage_bytes = self.opts.dump_detailed_report_at_memory_usage * 1024 * 1024

        if opts.dump_removed_short_ids:
            os.makedirs(opts.dump_removed_short_ids_path, exist_ok=True)

        # each time a network has an update regarding txs, blocks, etc. register in a dict,
        # this way can verify if node lost connection to requested relay.

        self.last_sync_message_received_by_network: Dict[int, float] = {}

        opts.has_fully_updated_tx_service = False
        self.alarm_queue.register_alarm(constants.TX_SERVICE_SYNC_PROGRESS_S, self._sync_tx_services)
        self._check_sync_relay_connections_alarm_id = self.alarm_queue.register_alarm(
            constants.LAST_MSG_FROM_RELAY_THRESHOLD_S, self._check_sync_relay_connections)
        self._transaction_sync_timeout_alarm_id = self.alarm_queue.register_alarm(
            constants.TX_SERVICE_CHECK_NETWORKS_SYNCED_S, self._transaction_sync_timeout)

    def get_sdn_address(self):
        """
        Placeholder for net event loop to get the sdn address (relay only).
        :return:
        """
        return

    @abstractmethod
    def get_tx_service(self, network_num=None):
        pass

    @abstractmethod
    def get_outbound_peer_addresses(self):
        pass

    @abstractmethod
    def get_broadcast_service(self) -> BroadcastService:
        pass

    @abstractmethod
    def send_request_for_relay_peers(self):
        pass

    @abstractmethod
    def build_connection(self, socket_connection: SocketConnection, ip: str, port: int, from_me: bool = False) \
            -> Optional[AbstractConnection]:
        pass

    @abstractmethod
    def on_failed_connection_retry(self, ip: str, port: int, connection_type: ConnectionType) -> None:
        pass

    @abstractmethod
    def _sync_tx_services(self):
        pass

    @abstractmethod
    def _transaction_sync_timeout(self):
        pass

    @abstractmethod
    def _check_sync_relay_connections(self):
        pass

    def connection_exists(self, ip, port):
        return self.connection_pool.has_connection(ip, port)

    def on_connection_added(self, socket_connection: SocketConnection, ip: str, port: int, from_me: bool):
        """
        Notifies the node that a connection is coming in.
        """
        # If we're already connected to the remote peer, log the event and request disconnect.
        if self.connection_exists(ip, port):
            logger.debug("Duplicate connection attempted to: {0}:{1}. Dropping.", ip, port)
            socket_connection.mark_for_close(should_retry=False)
        else:
            self._initialize_connection(socket_connection, ip, port, from_me)

    def on_connection_initialized(self, fileno: int):
        conn = self.connection_pool.get_by_fileno(fileno)

        if conn is None:
            logger.debug("Unexpectedly initialized connection not in pool. Fileno: {0}", fileno)
            return

        logger.debug("Connection initialized: {}", conn)
        conn.state |= ConnectionState.INITIALIZED

    def on_connection_closed(self, fileno: int):
        conn = self.connection_pool.get_by_fileno(fileno)

        if conn is None:
            logger.debug("Unexpectedly closed connection not in pool. Fileno: {0}", fileno)
            return

        logger.info("Closed connection: {}", conn)
        if conn.CONNECTION_TYPE == ConnectionType.BLOCKCHAIN_NODE:
            logger.info("Unable to connect to blockchain node on IP {} and port {}. Check that blockchain IP and port "
                        "are correct!", conn.peer_ip, conn.peer_port)
        self._destroy_conn(conn)

    def on_updated_peers(self, outbound_peer_models):
        if not outbound_peer_models:
            logger.debug("Got peer update with no peers.")
            return

        logger.debug("Processing updated outbound peers: {}.", outbound_peer_models)

        # Remove peers not in updated list or from command-line args.
        remove_peers = []
        old_peers = self.outbound_peers
        for old_peer in old_peers:
            if not (any(old_peer.ip == fixed_peer.ip and old_peer.port == fixed_peer.port
                        for fixed_peer in self.opts.outbound_peers)
                    or any(new_peer.ip == old_peer.ip and new_peer.port == old_peer.port
                           for new_peer in outbound_peer_models)):
                remove_peers.append(old_peer)

        for rem_peer in remove_peers:
            if self.connection_pool.has_connection(rem_peer.ip, rem_peer.port):
                rem_conn = self.connection_pool.get_by_ipport(rem_peer.ip, rem_peer.port)
                if rem_conn:
                    rem_conn.mark_for_close(False)

        # Connect to peers not in our known pool
        for peer in outbound_peer_models:
            peer_ip = peer.ip
            peer_port = peer.port
            if not self.connection_pool.has_connection(peer_ip, peer_port):
                self.enqueue_connection(peer_ip, peer_port)
        self.outbound_peers = outbound_peer_models

    def on_updated_sid_space(self, sid_start, sid_end):
        """
        Placeholder interface to receive sid updates from SDN over sockets and pass to relay node
        """
        return

    def on_bytes_received(self, fileno: int, bytes_received: bytearray) -> None:
        """
        :param fileno:
        :param bytes_received:
        :return: True if the node should continue receiving bytes from the remote peer. False otherwise.
        """
        conn = self.connection_pool.get_by_fileno(fileno)

        if conn is None:
            logger.debug("Received bytes for connection not in pool. Fileno: {0}", fileno)
            return

        if not conn.is_alive():
            conn.log_trace("Skipping receiving bytes for closed connection.")
            return

        conn.add_received_bytes(bytes_received)

    def on_finished_receiving(self, fileno):
        conn = self.connection_pool.get_by_fileno(fileno)

        if conn is None:
            logger.debug("Received bytes for connection not in pool. Fileno: {0}", fileno)
            return

        conn.process_message()

    def get_bytes_to_send(self, fileno):
        conn = self.connection_pool.get_by_fileno(fileno)

        if conn is None:
            logger.debug("Request to get bytes for connection not in pool. Fileno: {0}", fileno)
            return

        if not conn.is_alive():
            conn.log_trace("Skipping sending bytes for closed connection.")
            return

        return conn.get_bytes_to_send()

    def on_bytes_sent(self, fileno, bytes_sent):
        conn = self.connection_pool.get_by_fileno(fileno)

        if conn is None:
            logger.debug("Bytes sent call for connection not in pool. Fileno: {0}", fileno)
            return

        conn.advance_sent_bytes(bytes_sent)

    def fire_alarms(self) -> float:
        time_to_next = self.alarm_queue.fire_ready_alarms()
        if time_to_next is not None:
            return max(time_to_next, constants.MIN_SLEEP_TIMEOUT)
        else:
            return constants.MAX_EVENT_LOOP_TIMEOUT_S

    def force_exit(self):
        """
        Indicates if node should trigger exit in event loop. Primarily used for testing.

        Typically requires one additional socket call (e.g. connecting to this node via a socket)
        to finish terminating the event loop.
        """
        return self.should_force_exit

    def close(self):
        logger.error("Node is closing! Closing everything.")

        for _fileno, conn in self.connection_pool.items():
            self._destroy_conn(conn)
        self.cleanup_memory_stats_logging()

    def broadcast(self, msg: AbstractMessage, broadcasting_conn: Optional[AbstractConnection] = None,
                  prepend_to_queue: bool = False, connection_types: Optional[List[ConnectionType]] = None) \
            -> List[AbstractConnection]:
        """
        Broadcasts message msg to connections of the specified type except requester.
        """
        if connection_types is None:
            connection_types = [ConnectionType.RELAY_ALL]
        options = BroadcastOptions(broadcasting_conn, prepend_to_queue, connection_types)
        return self.broadcast_service.broadcast(msg, options)

    def enqueue_connection(self, ip: str, port: int):
        """
        Queues a connection up for the event loop to open a socket for.
        """
        logger.trace("Enqueuing connection to {}:{}", ip, port)
        self.connection_queue.append((ip, port))

    def pop_next_connection_address(self) -> Optional[Tuple[str, int]]:
        """
        Returns the next connection address for the event loop to initiate a socket connection to.
        """
        if self.connection_queue:
            return self.connection_queue.popleft()

        return

    def _destroy_conn(self, conn: AbstractConnection):
        """
        Clean up the associated connection and update all data structures tracking it.

        Do not call this function directly to close a connection, unless circumstances do not allow cleaning shutting
        down the node via event loop lifecycle hooks (e.g. immediate shutdown).

        In connection handlers, use `AbstractConnection#mark_for_close`, and the connection will be cleaned up as part
        of event handling.
        In other node lifecycle events, use `enqueue_disconnect` to allow the event loop to trigger connection cleanup.

        :param conn connection to destroy
        """
        should_retry = not bool(conn.socket_connection.state & SocketConnectionState.DO_NOT_RETRY)

        logger.debug("Breaking connection to {}. Attempting retry: {}", conn, should_retry)
        conn.dispose()
        self.connection_pool.delete(conn)

        peer_ip, peer_port = conn.peer_ip, conn.peer_port
        if should_retry and self.continue_retrying_connection(peer_ip, peer_port, conn.CONNECTION_TYPE):
            self.alarm_queue.register_alarm(self._get_next_retry_timeout(peer_ip, peer_port),
                                            self._retry_init_client_socket,
                                            peer_ip, peer_port, conn.CONNECTION_TYPE)
        else:
            self.on_failed_connection_retry(peer_ip, peer_port, conn.CONNECTION_TYPE)

    def continue_retrying_connection(self, ip: str, port: int, connection_type: ConnectionType) -> bool:
        """
        Indicates whether to continue retrying connection. For most connections, this will will stop
        at the maximum of constants.MAX_CONNECT_RETRIES, but some connections should be always retried
        unless there's some fatal socket error.
        """
        is_sdn = bool(connection_type & ConnectionType.SDN)
        return is_sdn or self.num_retries_by_ip[(ip, port)] < constants.MAX_CONNECT_RETRIES

    def init_throughput_logging(self):
        throughput_statistics.set_node(self)
        self.alarm_queue.register_alarm(constants.FIRST_STATS_INTERVAL_S, throughput_statistics.flush_info)

    def init_node_info_logging(self):
        node_info_statistics.set_node(self)
        self.alarm_queue.register_alarm(constants.FIRST_STATS_INTERVAL_S, node_info_statistics.flush_info)

    def init_memory_stats_logging(self):
        memory_statistics.set_node(self)
        memory_statistics.start_recording(self.record_mem_stats)

    def cleanup_memory_stats_logging(self):
        memory_statistics.stop_recording()

    def init_block_stats_logging(self):
        block_stats.set_node(self)

    def init_tx_stats_logging(self):
        tx_stats.set_node(self)

    def flush_all_send_buffers(self):
        for conn in self.connection_pool:
            if conn.socket_connection.can_send:
                conn.socket_connection.send()
        return self.FLUSH_SEND_BUFFERS_INTERVAL

    def record_mem_stats(self):
        """
        When overridden, records identified memory stats and flushes them to std out
        :returns memory stats flush interval
        """
        self.connection_pool.log_connection_pool_mem_stats()
        return memory_statistics.flush_info()

    def set_node_config_opts_from_sdn(self, opts):

        # TODO: currently hard-coding configuration values
        opts.stats_calculate_actual_size = False
        opts.log_detailed_block_stats = False

        blockchain_networks: List[BlockchainNetworkModel] = opts.blockchain_networks
        for blockchain_network in blockchain_networks:
            tx_stats.configure_network(blockchain_network.network_num, blockchain_network.tx_percent_to_log)

    def dump_memory_usage(self):
        total_mem_usage = memory_utils.get_app_memory_usage()

        if total_mem_usage >= self.next_report_mem_usage_bytes:
            node_size = memory_utils.get_detailed_object_size(self)
            memory_logger.statistics(
                "Application consumed {} bytes which is over set limit {} bytes. Detailed memory report: {}",
                total_mem_usage, self.next_report_mem_usage_bytes, json_utils.serialize(node_size))
            self.next_report_mem_usage_bytes = total_mem_usage + constants.MEMORY_USAGE_INCREASE_FOR_NEXT_REPORT_BYTES

    def on_input_received(self, file_no: int) -> bool:
        """handles an input event from the event loop

        :param file_no: the socket connection file_no
        :return: True if the connection is receivable, otherwise False
        """
        connection = self.connection_pool.get_by_fileno(file_no)
        if connection is None:
            return False
        return connection.on_input_received()

    def _initialize_connection(self, socket_connection: SocketConnection, ip: str, port: int, from_me: bool):
        conn_obj = self.build_connection(socket_connection, ip, port, from_me)
        if conn_obj is not None:
            logger.info("Connecting to: {}...", conn_obj)

            self.alarm_queue.register_alarm(constants.CONNECTION_TIMEOUT, self._connection_timeout, conn_obj)
            self.connection_pool.add(socket_connection.fileno(), ip, port, conn_obj)

            if conn_obj.CONNECTION_TYPE == ConnectionType.SDN:
                self.sdn_connection = conn_obj
        else:
            logger.warning("Could not determine expected connection type for {}:{}. Disconnecting...",
                           ip, port)
            socket_connection.mark_for_close(should_retry=False)

    def on_fully_updated_tx_service(self):
        logger.info("Synced transaction state with BDN.")
        self.opts.has_fully_updated_tx_service = True

    def _connection_timeout(self, conn: AbstractConnection) -> int:
        """
        Check if the connection is established.
        If it is not established, we give up for untrusted connections and try again for trusted connections.
        """

        logger.trace("Checking connection status: {}", conn)

        if conn.state & ConnectionState.ESTABLISHED:
            logger.trace("Connection is still established: {}", conn)

            return constants.CANCEL_ALARMS

        if not conn.is_alive():
            logger.trace("Connection has already been marked for close: {}", conn)
            return constants.CANCEL_ALARMS

        # Clean up the old connection and retry it if it is trusted
        logger.trace("Connection has timed out: {}", conn)
        conn.mark_for_close()

        # It is connect_to_address's job to schedule this function.
        return constants.CANCEL_ALARMS

    def _kill_node(self, _signum, _stack):
        """
        Kills the node immediately
        """
        self.should_force_exit = True
        raise TerminationError("Node killed.")

    def _get_next_retry_timeout(self, ip: str, port: int) -> int:
        """
        Returns Fibonnaci(n), where n is the number of retry attempts + 1, up to max of Fibonacci(8) == 13.
        """
        golden_ratio = (1 + 5 ** .5) / 2
        sequence_number = min(self.num_retries_by_ip[(ip, port)] + 1, constants.MAX_CONNECT_TIMEOUT_INCREASE)
        return int((golden_ratio ** sequence_number - (1 - golden_ratio) ** sequence_number) / 5 ** .5)

    def _retry_init_client_socket(self, ip: str, port: int, connection_type: ConnectionType):
        self.num_retries_by_ip[(ip, port)] += 1

        logger.debug("Retrying {} connection to {}:{}. Attempt #{}.", connection_type, ip, port,
                     self.num_retries_by_ip[(ip, port)])
        self.enqueue_connection(ip, port)

        # In case of connection retry to SDN - no need to resync transactions on this node, just update
        # 'has_fully_updated_tx_service' attribute on SDN since it was set to false when the connection was
        # lost.
        if connection_type == ConnectionType.SDN:
            self.on_fully_updated_tx_service()

        return 0
