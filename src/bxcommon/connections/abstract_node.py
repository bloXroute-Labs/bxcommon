import asyncio
import os
import time
from abc import ABCMeta, abstractmethod
from asyncio import Future
from collections import defaultdict, Counter
from ssl import SSLContext
from typing import List, Optional, Tuple, Dict, NamedTuple, Union, Set

import gc

from bxcommon import constants
from bxcommon.connections.abstract_connection import AbstractConnection
from bxcommon.connections.connection_pool import ConnectionPool
from bxcommon.connections.connection_state import ConnectionState
from bxcommon.connections.connection_type import ConnectionType
from bxcommon.exceptions import TerminationError
from bxcommon.messages.abstract_message import AbstractMessage
from bxcommon.models.authenticated_peer_info import AuthenticatedPeerInfo
from bxcommon.models.blockchain_network_model import BlockchainNetworkModel
from bxcommon.models.node_model import NodeModel
from bxcommon.models.node_type import NodeType
from bxcommon.models.outbound_peer_model import OutboundPeerModel
from bxcommon.network.abstract_socket_connection_protocol import AbstractSocketConnectionProtocol
from bxcommon.network.ip_endpoint import IpEndpoint
from bxcommon.network.peer_info import ConnectionPeerInfo
from bxcommon.network.socket_connection_state import SocketConnectionStates
from bxcommon.services import sdn_http_service
from bxcommon.services.broadcast_service import BroadcastService, \
    BroadcastOptions
from bxcommon.services.threaded_request_service import ThreadedRequestService
from bxcommon.services.transaction_service import TransactionService
from bxcommon.storage.serialized_message_cache import SerializedMessageCache
from bxcommon.utils import memory_utils, convert, performance_utils
from bxcommon.utils.alarm_queue import AlarmQueue, AlarmId
from bxcommon.utils.blockchain_utils import bdn_tx_to_bx_tx
from bxcommon.common_opts import CommonOpts
from bxcommon.utils.expiring_dict import ExpiringDict
from bxcommon.utils.stats.block_statistics_service import block_stats
from bxcommon.utils.stats.memory_statistics_service import memory_statistics
from bxcommon.utils.stats.node_info_service import node_info_statistics
from bxcommon.utils.stats.node_statistics_service import node_stats_service
from bxcommon.utils.stats.throughput_service import throughput_statistics
from bxcommon.utils.stats.transaction_statistics_service import tx_stats
from bxcommon.utils.transaction_short_id_buckets import TransactionShortIdBuckets
from bxutils import log_messages, utils
from bxutils import logging
from bxutils.exceptions.connection_authentication_error import \
    ConnectionAuthenticationError
from bxutils.logging import LogRecordType, LogLevel
from bxutils.services.node_ssl_service import NodeSSLService
from bxutils.ssl.extensions import extensions_factory
from bxutils.ssl.ssl_certificate_type import SSLCertificateType


logger = logging.get_logger(__name__)
memory_logger = logging.get_logger(LogRecordType.BxMemory, __name__)
performance_troubleshooting_logger = logging.get_logger(LogRecordType.PerformanceTroubleshooting, __name__)


class DisconnectRequest(NamedTuple):
    file_no: int
    should_retry: bool


# pylint: disable=too-many-public-methods
class AbstractNode:
    __meta__ = ABCMeta
    FLUSH_SEND_BUFFERS_INTERVAL = constants.OUTPUT_BUFFER_BATCH_MAX_HOLD_TIME * 2
    NODE_TYPE: Optional[NodeType] = None

    def __init__(
        self,
        opts: CommonOpts,
        node_ssl_service: NodeSSLService,
        connection_pool: Optional[ConnectionPool] = None
    ):
        # Event handling queue for delayed events
        self.alarm_queue = AlarmQueue()
        self.node_ssl_service = node_ssl_service
        logger.debug("Initializing node of type: {}", self.NODE_TYPE)
        self.server_endpoints = [
            IpEndpoint(constants.LISTEN_ON_IP_ADDRESS, opts.external_port),
            # TODO: remove this after v1 is no longer supported
            IpEndpoint(constants.LISTEN_ON_IP_ADDRESS, opts.non_ssl_port)
        ]

        self.set_node_config_opts_from_sdn(opts)
        self.opts: CommonOpts = opts
        self.pending_connection_requests: Set[ConnectionPeerInfo] = set()
        self.pending_connection_attempts: Set[ConnectionPeerInfo] = set()
        self.recent_connections: ExpiringDict[str, int] = ExpiringDict(
            self.alarm_queue,
            constants.THROTTLE_RECONNECT_TIME_S,
            name="recent_connections"
        )
        self.outbound_peers: Set[OutboundPeerModel] = opts.outbound_peers.copy()

        if connection_pool is not None:
            self.connection_pool = connection_pool
        else:
            self.connection_pool = ConnectionPool()

        self.should_force_exit = False
        self.should_restart_on_high_memory = False

        self.num_retries_by_ip: Dict[Tuple[str, int], int] = defaultdict(int)

        self.init_node_status_logging()
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

        self.start_sync_time: Optional[float] = None
        self.sync_metrics: Dict[int, Counter] = defaultdict(Counter)
        self.sync_short_id_buckets: Dict[int, TransactionShortIdBuckets] = defaultdict(TransactionShortIdBuckets)

        opts.has_fully_updated_tx_service = False

        self.check_sync_relay_connections_alarm_id: Optional[AlarmId] = None
        self.transaction_sync_timeout_alarm_id: Optional[AlarmId] = None

        self.requester = ThreadedRequestService(
            # pyre-fixme[16]: `Optional` has no attribute `name`.
            self.NODE_TYPE.name.lower(), self.alarm_queue, constants.THREADED_HTTP_POOL_SLEEP_INTERVAL_S
        )

        self._last_responsiveness_check_log_time = time.time()
        self._last_responsiveness_check_details = {}
        self.gc_logging_enabled = False
        self.serialized_message_cache = SerializedMessageCache(self.alarm_queue)

        self.alarm_queue.register_alarm(constants.RESPONSIVENESS_CHECK_INTERVAL_S, self._responsiveness_check_log)

    def get_sdn_address(self):
        """
        Placeholder for net event loop to get the sdn address (relay only).
        :return:
        """
        return

    @abstractmethod
    def get_tx_service(self, network_num: Optional[int] = None) -> TransactionService:
        pass

    @abstractmethod
    def get_outbound_peer_info(self) -> List[ConnectionPeerInfo]:
        pass

    @abstractmethod
    def get_broadcast_service(self) -> BroadcastService:
        pass

    def sync_and_send_request_for_relay_peers(self, network_num: int) -> int:
        """
        Requests potential relay peers from SDN. Merges list with provided command line relays.

        This function retrieves from the SDN potential_relay_peers_by_network
        Then it try to ping for each relay (timeout of 2 seconds). The ping is done in parallel
        Once there are ping result, it calculate the best relay and decides if need to switch relays

        The above can take time, so the functions is split into several internal functions and use the thread pool
        not to block the main thread.
        """

        self.requester.send_threaded_request(
            sdn_http_service.fetch_potential_relay_peers_by_network,
            self.opts.node_id,
            network_num,
            # pyre-fixme[6]: Expected `Optional[Callable[[Future[Any]], Any]]` for 4th parameter `done_callback`
            #  to call `send_threaded_request` but got `BoundMethod[Callable(_process_blockchain_network_from_sdn)
            #  [[Named(self, AbstractRelayConnection), Named(get_blockchain_network_future, Future[Any])], Any],
            #  AbstractRelayConnection]`.
            done_callback=self.process_potential_relays_from_sdn
        )

        return constants.CANCEL_ALARMS

    def process_potential_relays_from_sdn(self, get_potential_relays_future: Future):
        pass

    @abstractmethod
    def build_connection(self, socket_connection: AbstractSocketConnectionProtocol) -> Optional[AbstractConnection]:
        pass

    @abstractmethod
    def on_failed_connection_retry(
        self, ip: str, port: int, connection_type: ConnectionType, connection_state: ConnectionState
    ) -> None:
        pass

    def report_connection_attempt(self, ip_address: str) -> int:
        if ip_address in self.recent_connections:
            self.recent_connections[ip_address] += 1
        else:
            self.recent_connections.add(ip_address, 1)
        return self.recent_connections[ip_address]

    def connection_exists(
        self,
        ip: str,
        port: int,
        peer_id: Optional[str] = None
    ) -> bool:
        return self.connection_pool.has_connection(ip, port, peer_id)

    def on_connection_added(self, socket_connection: AbstractSocketConnectionProtocol) -> Optional[AbstractConnection]:
        """
        Notifies the node that a connection is coming in.
        """
        # If we're already connected to the remote peer, log the event and request disconnect.
        self.pending_connection_attempts.discard(
            ConnectionPeerInfo(socket_connection.endpoint, AbstractConnection.CONNECTION_TYPE)
        )
        ip, port = socket_connection.endpoint
        peer_info: Optional[AuthenticatedPeerInfo] = None
        if socket_connection.is_ssl:
            try:
                peer_info = self._get_socket_peer_info(
                    socket_connection
                )
            except ConnectionAuthenticationError as e:
                logger.warning(log_messages.FAILED_TO_AUTHENTICATE_CONNECTION, ip, port, e)
                socket_connection.mark_for_close(should_retry=False)
                return None

            if self.connection_exists(ip, port, peer_info.peer_id)\
                    and peer_info.connection_type != ConnectionType.RELAY_PROXY:
                logger.debug(
                    "Duplicate connection attempted to: {}:{} (peer id: {}). "
                    "Dropping.",
                    ip,
                    port,
                    peer_info.peer_id
                )
                socket_connection.mark_for_close(should_retry=False)
                return None
        elif self.connection_exists(ip, port):
            logger.debug(
                "Duplicate connection attempt to {}:{}. Dropping.",
                ip,
                port,
            )
            socket_connection.mark_for_close(should_retry=False)
            return None

        connection = self._initialize_connection(socket_connection)
        if connection is None:
            return None

        if peer_info is not None:
            connection.on_connection_authenticated(
                peer_info
            )
            self.connection_pool.index_conn_node_id(
                peer_info.peer_id, connection
            )

        connection.state |= ConnectionState.INITIALIZED
        logger.debug("Successfully initialized connection: {}", connection)
        return connection

    def on_connection_closed(self, file_no: int, mark_connection_for_close: bool = False):
        conn = self.connection_pool.get_by_fileno(file_no)

        if conn is None:
            logger.debug("Unexpectedly closed connection not in pool. file_no: {}", file_no)
            return

        if mark_connection_for_close:
            conn.mark_for_close()

        self._destroy_conn(conn)

    def log_refused_connection(self, peer_info: ConnectionPeerInfo, error: str):
        logger.info("Failed to connect to: {}, {}.", peer_info, error)

    def log_closed_connection(self, connection: AbstractConnection):
        if not connection.established:
            logger.info("Failed to connect to: {}.", connection)
        else:
            logger.info("Closed connection: {}", connection)

    def on_updated_peers(self, outbound_peer_models: Set[OutboundPeerModel]) -> None:
        if not outbound_peer_models:
            logger.debug("Got peer update with no peers.")
            return

        logger.debug("Processing updated outbound peers: {}.", outbound_peer_models)

        # Remove peers not in updated list or from command-line args.
        old_peers = self.outbound_peers

        # TODO: remove casting to set once the type of outbound peer model is verified globally
        remove_peers = set(old_peers) - set(outbound_peer_models) - set(self.opts.outbound_peers)

        for rem_peer in remove_peers:
            if self.connection_pool.has_connection(
                rem_peer.ip,
                rem_peer.port,
                rem_peer.node_id
            ):
                rem_conn = self.connection_pool.get_by_ipport(
                    rem_peer.ip, rem_peer.port, rem_peer.node_id
                )
                if rem_conn:
                    rem_conn.mark_for_close(False)

        # Connect to peers not in our known pool or in opts.outbound_peers
        new_peer_models = set()
        new_peer_models.update(old_peers)
        new_peer_models.update(outbound_peer_models)
        new_peer_models.difference_update(remove_peers)
        for peer in new_peer_models:
            peer_ip = peer.ip
            peer_port = peer.port
            if self.should_connect_to_new_outbound_peer(peer):
                self.enqueue_connection(
                    peer_ip, peer_port, convert.peer_node_to_connection_type(
                        # pyre-fixme[6]: Expected `NodeType` for 1st param but got
                        #  `Optional[NodeType]`.
                        self.NODE_TYPE, peer.node_type
                    )
                )
        self.outbound_peers = new_peer_models

    def on_updated_node_model(self, new_node_model: NodeModel):
        """
        Updates `opts` according a newly updated `NodeModel`.
        This is currently unused on gateways.
        """
        logger.debug(
            "Updating node attributes with new model: {}", new_node_model
        )
        for key, val in new_node_model.__dict__.items():
            logger.trace(
                "Updating attribute '{}': {} => {}", key, self.opts.__dict__.get(key, 'None'), val
            )
            self.opts.__dict__[key] = val

    def should_connect_to_new_outbound_peer(self, outbound_peer: OutboundPeerModel) -> bool:
        return not self.connection_pool.has_connection(
            outbound_peer.ip, outbound_peer.port, outbound_peer.node_id
        )

    def on_bytes_received(self, file_no: int, bytes_received: Union[bytearray, bytes]) -> None:
        """
        :param file_no:
        :param bytes_received:
        :return: True if the node should continue receiving bytes from the remote peer. False otherwise.
        """
        conn = self.connection_pool.get_by_fileno(file_no)

        if conn is None:
            logger.debug("Received bytes for connection not in pool. file_no: {0}", file_no)
            return

        if not conn.is_alive():
            conn.log_trace("Skipping receiving bytes for closed connection.")
            return

        conn.add_received_bytes(bytes_received)
        conn.process_message()

    def get_bytes_to_send(self, file_no: int) -> Optional[memoryview]:
        conn = self.connection_pool.get_by_fileno(file_no)

        if conn is None:
            logger.debug("Request to get bytes for connection not in pool. file_no: {}", file_no)
            return None

        if not conn.is_alive():
            conn.log_trace("Skipping sending bytes for closed connection.")
            return None

        return conn.get_bytes_to_send()

    def on_bytes_sent(self, file_no: int, bytes_sent: int):
        conn = self.connection_pool.get_by_fileno(file_no)

        if conn is None:
            logger.debug("Bytes sent call for connection not in pool. file_no: {0}", file_no)
            return

        conn.advance_sent_bytes(bytes_sent)

    def fire_alarms(self) -> float:
        time_to_next = self.alarm_queue.fire_ready_alarms()
        if time_to_next is not None:
            return time_to_next
        else:
            return constants.MAX_EVENT_LOOP_TIMEOUT

    def force_exit(self):
        """
        Indicates if node should trigger exit in event loop. Primarily used for testing.

        Typically requires one additional socket call (e.g. connecting to this node via a socket)
        to finish terminating the event loop.
        """
        return self.should_force_exit

    async def close(self):
        logger.info("Node is closing! Closing everything.")

        shutdown_task = asyncio.ensure_future(self.close_all_connections())
        try:
            await asyncio.wait_for(shutdown_task, constants.NODE_SHUTDOWN_TIMEOUT_S)
        except Exception as e:  # pylint: disable=broad-except
            logger.exception("Node shutdown failed due to an error: {}, force closing!", e)
        self.requester.close()
        self.cleanup_memory_stats_logging()

    async def close_all_connections(self):
        """
        Closes all connections from the node
        """
        for _, conn in self.connection_pool.items():
            conn.mark_for_close(should_retry=False)

    def broadcast(
        self,
        msg: AbstractMessage,
        broadcasting_conn: Optional[AbstractConnection] = None,
        prepend_to_queue: bool = False,
        connection_types: Optional[Tuple[ConnectionType, ...]] = None
    ) -> List[AbstractConnection]:
        """
        Broadcasts message msg to connections of the specified type except requester.
        """
        if connection_types is None:
            connection_types = (ConnectionType.RELAY_ALL,)
        options = BroadcastOptions(broadcasting_conn, prepend_to_queue, connection_types)
        connections = self.broadcast_service.broadcast(msg, options)
        return connections

    def enqueue_connection(self, ip: str, port: int, connection_type: ConnectionType):
        """
        Queues a connection up for the event loop to open a socket for.
        """
        peer_info = ConnectionPeerInfo(IpEndpoint(ip, port), connection_type)
        if peer_info in self.pending_connection_attempts:
            logger.debug("Not adding {}, waiting until connection attempt to complete", peer_info)
        else:
            logger.trace("Enqueuing connection: {}.", peer_info)
            self.pending_connection_requests.add(peer_info)

    def dequeue_connection_requests(self) -> Optional[Set[ConnectionPeerInfo]]:
        """
        Returns the pending connection requests for the event loop to initiate a socket connection to.
        """
        if self.pending_connection_requests:
            pending_connection_requests = self.pending_connection_requests
            self.pending_connection_requests = set()
            self.pending_connection_attempts.update(pending_connection_requests)
            return pending_connection_requests
        else:
            return None

    def continue_retrying_connection(self, ip: str, port: int, connection_type: ConnectionType) -> bool:
        """
        Indicates whether to continue retrying connection. For most connections, this will will stop
        at the maximum of constants.MAX_CONNECT_RETRIES, but some connections should be always retried
        unless there's some fatal socket error.
        """
        is_sdn = ConnectionType.SDN in connection_type
        return is_sdn or self.num_retries_by_ip[(ip, port)] < constants.MAX_CONNECT_RETRIES

    def init_node_status_logging(self):
        node_stats_service.set_node(self)
        self.alarm_queue.register_alarm(constants.FIRST_STATS_INTERVAL_S, node_stats_service.flush_info)

    def init_throughput_logging(self):
        throughput_statistics.set_node(self)
        self.alarm_queue.register_alarm(constants.FIRST_STATS_INTERVAL_S, throughput_statistics.flush_info)

    def init_node_info_logging(self):
        node_info_statistics.set_node(self)
        self.alarm_queue.register_alarm(constants.FIRST_STATS_INTERVAL_S, node_info_statistics.flush_info)

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

    def record_mem_stats(self, low_threshold: int, medium_threshold: int, high_threshold: int):
        """
        When overridden, records identified memory stats and flushes them to std out
        :returns memory stats flush interval
        """
        total_memory = memory_utils.get_app_memory_usage()
        if total_memory > low_threshold:
            gc.collect()
            total_memory = memory_utils.get_app_memory_usage()
        self._record_mem_stats(total_memory > medium_threshold)

        return memory_statistics.flush_info(high_threshold)

    def _record_mem_stats(self, include_data_structure_memory: bool = False):
        if include_data_structure_memory:
            self.connection_pool.log_connection_pool_mem_stats()

    def set_node_config_opts_from_sdn(self, opts: CommonOpts) -> None:
        blockchain_networks: Dict[int, BlockchainNetworkModel] = opts.blockchain_networks
        for blockchain_network in blockchain_networks.values():
            tx_stats.configure_network(
                blockchain_network.network_num,
                blockchain_network.tx_percent_to_log_by_hash,
                blockchain_network.tx_percent_to_log_by_sid
            )
        bdn_tx_to_bx_tx.init(blockchain_networks)

    def dump_memory_usage(self, total_memory: int, threshold: int):
        if total_memory > threshold and logger.isEnabledFor(LogLevel.DEBUG):
            node_size = self.get_node_memory_size()
            memory_logger.debug(
                "Application consumed {} bytes which is over set limit {} bytes. Detailed memory report: {}",
                total_memory,
                threshold,
                node_size
            )

    def get_node_memory_size(self):
        return memory_utils.get_detailed_object_size(self)

    def on_input_received(self, file_no: int) -> bool:
        """handles an input event from the event loop

        :param file_no: the socket connection file_no
        :return: True if the connection is receivable, otherwise False
        """
        connection = self.connection_pool.get_by_fileno(file_no)
        if connection is None:
            return False
        return connection.on_input_received()

    async def init(self) -> None:
        self.requester.start()

    def handle_connection_closed(
        self, should_retry: bool, peer_info: ConnectionPeerInfo, connection_state: ConnectionState
    ) -> None:
        self.pending_connection_attempts.discard(peer_info)
        peer_ip, peer_port = peer_info.endpoint
        connection_type = peer_info.connection_type
        if should_retry and self.continue_retrying_connection(peer_ip, peer_port, connection_type):
            self.alarm_queue.register_alarm(
                self._get_next_retry_timeout(peer_ip, peer_port),
                self._retry_init_client_socket,
                peer_ip, peer_port, connection_type
            )
        else:
            self.on_failed_connection_retry(peer_ip, peer_port, connection_type, connection_state)

    def get_server_ssl_ctx(self) -> SSLContext:
        return self.node_ssl_service.create_ssl_context(SSLCertificateType.PRIVATE)

    def get_target_ssl_ctx(self, endpoint: IpEndpoint, connection_type: ConnectionType) -> SSLContext:
        logger.trace("Fetching SSL certificate for: {} ({}).", endpoint, connection_type)
        return self.node_ssl_service.create_ssl_context(SSLCertificateType.PRIVATE)

    @abstractmethod
    def reevaluate_transaction_streamer_connection(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def on_new_subscriber_request(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def init_memory_stats_logging(self):
        raise NotImplementedError

    @abstractmethod
    def sync_tx_services(self):
        self.start_sync_time = time.time()
        self.sync_metrics = defaultdict(Counter)

    @abstractmethod
    def _transaction_sync_timeout(self) -> int:
        pass

    @abstractmethod
    def check_sync_relay_connections(self, conn: AbstractConnection) -> int:
        pass

    def _get_socket_peer_info(self, sock: AbstractSocketConnectionProtocol) -> AuthenticatedPeerInfo:
        assert sock.is_ssl
        assert self.NODE_TYPE is not None

        cert = sock.get_peer_certificate()
        node_type = extensions_factory.get_node_type(cert)
        try:
            connection_type = convert.peer_node_to_connection_type(
                # pyre-fixme[6]: Expected `NodeType` for 1st param but got
                #  `Optional[NodeType]`.
                self.NODE_TYPE, node_type
            )
        except (KeyError, ValueError):
            raise ConnectionAuthenticationError(
                f"Peer ssl certificate ({cert}) has an invalid node type: {node_type}!"
            )
        peer_id = extensions_factory.get_node_id(cert)
        if peer_id is None:
            raise ConnectionAuthenticationError(
                f"Peer ssl certificate ({cert}) does not contain a node id!")

        account_id = extensions_factory.get_account_id(cert)
        node_privileges = extensions_factory.get_node_privileges(cert)
        return AuthenticatedPeerInfo(connection_type, peer_id, account_id, node_privileges)

    def _should_log_closed_connection(self, _connection: AbstractConnection) -> bool:
        return True

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

        if self._should_log_closed_connection(conn):
            self.log_closed_connection(conn)

        should_retry = SocketConnectionStates.DO_NOT_RETRY not in conn.socket_connection.state

        logger.debug("Breaking connection to {}. Attempting retry: {}", conn, should_retry)

        self.connection_pool.delete(conn)
        self.handle_connection_closed(
            should_retry, ConnectionPeerInfo(conn.endpoint, conn.CONNECTION_TYPE), conn.state
        )
        conn.dispose()

    def _initialize_connection(
        self, socket_connection: AbstractSocketConnectionProtocol
    ) -> Optional[AbstractConnection]:
        conn_obj = self.build_connection(socket_connection)
        ip, port = socket_connection.endpoint
        if conn_obj is not None:
            logger.debug("Connecting to: {}...", conn_obj)

            self.alarm_queue.register_alarm(constants.CONNECTION_TIMEOUT, self._connection_timeout, conn_obj)
            self.connection_pool.add(socket_connection.file_no, ip, port, conn_obj)

            if conn_obj.CONNECTION_TYPE == ConnectionType.SDN:
                # pyre-fixme[16]: `AbstractNode` has no attribute `sdn_connection`.
                self.sdn_connection = conn_obj
        else:
            logger.warning(log_messages.UNABLE_TO_DETERMINE_CONNECTION_TYPE, ip, port)
            socket_connection.mark_for_close(should_retry=False)

        return conn_obj

    def on_network_synced(self, network_num: int) -> None:
        if network_num in self.last_sync_message_received_by_network:
            del self.last_sync_message_received_by_network[network_num]

    def on_fully_updated_tx_service(self):
        logger.debug(
            "Synced transaction state with BDN, last_sync_message_received_by_network: {}",
            self.last_sync_message_received_by_network
        )
        self.opts.has_fully_updated_tx_service = True

    def _connection_timeout(self, conn: AbstractConnection) -> int:
        """
        Check if the connection is established.
        If it is not established, we give up for untrusted connections and try again for trusted connections.
        """

        logger.trace("Checking connection status: {}", conn)

        if conn.established:
            logger.trace("Connection is still established: {}", conn)
            self.num_retries_by_ip[(conn.peer_ip, conn.peer_port)] = 0
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
        sequence_number = min(self.num_retries_by_ip[(ip, port)] + 1, constants.MAX_CONNECT_TIMEOUT_INCREASE)
        return utils.fibonacci(sequence_number)

    def _retry_init_client_socket(self, ip: str, port: int, connection_type: ConnectionType):
        self.num_retries_by_ip[(ip, port)] += 1

        logger.debug("Retrying {} connection to {}:{}. Attempt #{}.", connection_type, ip, port,
                     self.num_retries_by_ip[(ip, port)])
        self.enqueue_connection(ip, port, connection_type)

        return 0

    def _responsiveness_check_log(self):
        details = ""
        if self.gc_logging_enabled:
            gen0_stats, gen1_stats, gen2_stats = gc.get_stats()

            last_gen0_collections = self._last_responsiveness_check_details.get(
                "gen0_collections", 0
            )
            last_gen1_collections = self._last_responsiveness_check_details.get(
                "gen1_collections", 0
            )
            last_gen2_collections = self._last_responsiveness_check_details.get(
                "gen2_collections", 0
            )

            gen0_diff = gen0_stats["collections"] - last_gen0_collections
            gen1_diff = gen1_stats["collections"] - last_gen1_collections
            gen2_diff = gen2_stats["collections"] - last_gen2_collections

            details = (
                f"gen0_collections: {gen0_diff}, gen1_collections: {gen1_diff}, "
                f"gen2_collections: {gen2_diff}"
            )
            self._last_responsiveness_check_details.update({
                "gen0_collections": gen0_stats["collections"],
                "gen1_collections": gen1_stats["collections"],
                "gen2_collections": gen2_stats["collections"],
            })

        performance_utils.log_operation_duration(
            performance_troubleshooting_logger,
            "Responsiveness Check",
            self._last_responsiveness_check_log_time,
            constants.RESPONSIVENESS_CHECK_INTERVAL_S + constants.RESPONSIVENESS_CHECK_DELAY_WARN_THRESHOLD_S,
            details=details
        )
        self._last_responsiveness_check_log_time = time.time()
        return constants.RESPONSIVENESS_CHECK_INTERVAL_S
