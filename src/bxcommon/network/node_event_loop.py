import asyncio
import functools
import signal
import socket
from asyncio import CancelledError, Future
from asyncio.events import AbstractServer
from ssl import SSLContext
from typing import Iterator, List, Coroutine, Generator, Callable, Awaitable, Optional

from bxcommon import constants
from bxcommon.connections.abstract_node import AbstractNode
from bxcommon.connections.connection_state import ConnectionState
from bxcommon.connections.connection_type import ConnectionType
from bxcommon.exceptions import HighMemoryError, FeedSubscriptionTimeoutError
from bxcommon.network.base_socket_connection_protocol import BaseSocketConnectionProtocol
from bxcommon.network.ip_endpoint import IpEndpoint
from bxcommon.network.peer_info import ConnectionPeerInfo
from bxcommon.network.transport_layer_protocol import TransportLayerProtocol
from bxcommon.utils.expiring_dict import ExpiringDict
from bxutils import logging, constants as utils_constants

logger = logging.get_logger(__name__)


async def run_until_other_completed(
    callback: Callable[..., Awaitable], tsk_future: Future, wait_future: Future
) -> None:
    done = False
    future_to_set: Optional[Future] = tsk_future
    while not done:
        await callback()
        done = wait_future.done()
        if future_to_set is not None:
            future_to_set.set_result(True)
            future_to_set = None


class NodeEventLoop:
    _node: AbstractNode
    _stop_requested: bool

    def __init__(self, node: AbstractNode) -> None:
        self._node = node
        self._stop_requested = False
        loop = asyncio.get_event_loop()
        self._started = loop.create_future()
        loop.add_signal_handler(signal.SIGTERM, self.stop)
        loop.add_signal_handler(signal.SIGINT, self.stop)
        loop.add_signal_handler(signal.SIGSEGV, self.stop)

        self.connected_peers = ExpiringDict(
            self._node.alarm_queue,
            constants.THROTTLE_RECONNECT_TIME_S,
            name="throttle_reconnect"
        )

    async def run(self) -> None:
        try:
            await self._run()
        except HighMemoryError as e:
            raise e
        except FeedSubscriptionTimeoutError as e:
            raise e
        except Exception as e: # pylint: disable=broad-except
            logger.exception("Unhandled error raised: {}.", e)

    async def close(self) -> None:
        await self._node.close()

    def stop(self) -> None:
        logger.info("Stopping node event loop due to a termination request.")
        self._node.should_force_exit = True
        self._stop_requested = True

    async def wait_started(self) -> None:
        if self._started is not None:
            await self._started
            self._started = None

    async def _run(self) -> None:
        node_servers = await self._create_servers()
        try:
            await self._node.init()
            loop = asyncio.get_event_loop()
            await self._connect_to_peers()
            self._node.fire_alarms()
            self._started.set_result(True)
            while not self._stop_requested:
                node_future = loop.create_future()
                connection_future = loop.create_future()
                await asyncio.gather(
                    run_until_other_completed(self._perform_node_tasks, node_future, connection_future),
                    run_until_other_completed(self._process_new_connections_requests, connection_future, node_future)
                )
                if self._node.force_exit():
                    logger.info("Ending event loop. Shutdown has been requested.")
                    break
        finally:
            await self.close()
            for server in node_servers:
                server.close()
        if self._node.should_restart_on_high_memory:
            raise HighMemoryError()

    async def _process_new_connections_requests(self) -> None:
        peers_info = self._node.dequeue_connection_requests()
        if peers_info is not None:
            await asyncio.gather(*self._gather_connections(iter(peers_info)))
        else:
            await asyncio.sleep(constants.MAX_EVENT_LOOP_TIMEOUT)

    async def _connect_to_peers(self) -> None:
        connection_futures = self._gather_connections(self._iter_outbound_peers())
        if connection_futures:
            await asyncio.gather(*connection_futures)

    async def _create_servers(self) -> List[AbstractServer]:
        loop = asyncio.get_event_loop()
        endpoints = self._node.server_endpoints
        server_futures = []
        for endpoint in endpoints:
            if not endpoint.port:
                logger.debug("Endpoint: {} ,port is required, skipping", endpoint)
                continue
            ssl_ctx = None
            if endpoint.port in utils_constants.SSL_PORT_RANGE:
                ssl_ctx = self._node.get_server_ssl_ctx()
            server_future = loop.create_server(
                functools.partial(self._protocol_factory, endpoint, True),
                endpoint.ip_address,
                endpoint.port,
                family=socket.AF_INET,
                backlog=constants.DEFAULT_NODE_BACKLOG,
                reuse_address=True,
                ssl=ssl_ctx
            )
            server_futures.append(server_future)
        logger.debug("Starting listening on: {}.", endpoints)
        # pyre-fixme[7]: Expected `List[AbstractServer]` but got `Tuple[typing.Any]`.
        return await asyncio.gather(*server_futures)

    async def _connect_to_target(
        self,
        peer_info: ConnectionPeerInfo
    ) -> None:
        logger.debug("Connecting to {}.", peer_info)
        loop = asyncio.get_event_loop()
        target_endpoint = peer_info.endpoint
        try:
            if peer_info.transport_protocol == TransportLayerProtocol.TCP:
                ssl_ctx = self._get_target_ssl_context(target_endpoint, peer_info.connection_type)
                conn_task = asyncio.ensure_future(loop.create_connection(
                    functools.partial(self._protocol_factory, target_endpoint),
                    target_endpoint.ip_address,
                    target_endpoint.port,
                    family=socket.AF_INET,
                    ssl=ssl_ctx
                ))
            else:
                conn_task = asyncio.ensure_future(loop.create_datagram_endpoint(
                    functools.partial(self._protocol_factory, target_endpoint, is_ssl=False),
                    remote_addr=(target_endpoint.ip_address, target_endpoint.port),
                    family=socket.AF_INET
                ))
            await asyncio.wait_for(conn_task, constants.CONNECTION_TIMEOUT)
        except (
            TimeoutError,
            asyncio.TimeoutError,
            CancelledError,
            ConnectionRefusedError,
            ConnectionResetError,
            OSError,
        ) as e:
            err = str(e)
            if not err:
                err = repr(e)

            self._node.log_refused_connection(peer_info, err)
            self._node.handle_connection_closed(True, peer_info, ConnectionState.ESTABLISHED)

    def _iter_outbound_peers(self) -> Generator[ConnectionPeerInfo, None, None]:
        sdn_address = self._node.get_sdn_address()
        if sdn_address:
            yield ConnectionPeerInfo(IpEndpoint(*sdn_address), ConnectionType.SDN)
        else:
            logger.debug("SDN address not provided, skipping connection. This is expected for gateways.")
        for peer_info in self._node.get_outbound_peer_info():
            yield peer_info

    def _gather_connections(
        self, connections_info: Iterator[ConnectionPeerInfo]
    ) -> List[Coroutine]:
        return [
            self._connect_to_target(peer_info) for peer_info in connections_info
        ]

    def _get_target_ssl_context(self, endpoint: IpEndpoint, connection_type: ConnectionType) -> Optional[SSLContext]:
        if endpoint.port in utils_constants.SSL_PORT_RANGE:
            return self._node.get_target_ssl_ctx(endpoint, connection_type)
        else:
            return None

    async def _perform_node_tasks(self) -> None:
        timeout = self._node.fire_alarms()
        self._node.flush_all_send_buffers()
        if timeout is None or timeout < 0:
            timeout = constants.MAX_EVENT_LOOP_TIMEOUT
        else:
            timeout = min(timeout, constants.MAX_EVENT_LOOP_TIMEOUT)
        await asyncio.sleep(timeout)

    def _protocol_factory(
        self,
        endpoint: IpEndpoint,
        is_server: bool = False,
        is_ssl: Optional[bool] = None
    ) -> BaseSocketConnectionProtocol:
        if is_server:
            target_endpoint = None
        else:
            target_endpoint = endpoint

        if is_ssl is None:
            is_ssl = endpoint.port in utils_constants.SSL_PORT_RANGE

        return BaseSocketConnectionProtocol(self._node, target_endpoint, is_ssl=is_ssl)
