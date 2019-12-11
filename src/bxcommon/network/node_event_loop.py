import asyncio
import socket
from asyncio import CancelledError, Future
from asyncio.events import AbstractServer
from typing import Iterator, List, Coroutine, Generator, Callable, Awaitable, Optional

from bxcommon import constants
from bxcommon.connections.abstract_node import AbstractNode
from bxcommon.connections.connection_type import ConnectionType
from bxcommon.network.ip_endpoint import IpEndpoint
from bxcommon.network.peer_info import ConnectionPeerInfo
from bxcommon.network.socket_connection_protocol import SocketConnectionProtocol
from bxcommon.network.transport_layer_protocol import TransportLayerProtocol
from bxutils import logging

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

    def __init__(self, node: AbstractNode):
        self._node = node
        self._stop_requested = False
        loop = asyncio.get_event_loop()
        self._started = loop.create_future()

    async def run(self) -> None:
        try:
            await self._run()
        finally:
            await self.close()

    async def close(self) -> None:
        self._node.close()

    def stop(self) -> None:
        self._stop_requested = True

    async def wait_started(self) -> None:
        if self._started is not None:
            await self._started
            self._started = None

    async def _run(self) -> None:
        await self._node.init()
        node_server = await self._create_server()
        loop = asyncio.get_event_loop()
        async with node_server:
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
                    self.stop()
                    logger.info("Ending event loop. Shutdown has been requested manually.")
                    break

    async def _process_new_connections_requests(self):
        peer_info = self._node.pop_next_connection_request()
        peers_info = []
        while peer_info is not None:
            peers_info.append(peer_info)
            peer_info = self._node.pop_next_connection_request()
        if peers_info:
            await asyncio.gather(*self._gather_connections(iter(peers_info)))
        else:
            await asyncio.sleep(constants.MAX_EVENT_LOOP_TIMEOUT)

    async def _connect_to_peers(self) -> None:
        connection_futures = self._gather_connections(self._iter_outbound_peers())
        if connection_futures:
            await asyncio.gather(*connection_futures)

    async def _create_server(self) -> AbstractServer:
        loop = asyncio.get_running_loop()
        endpoint = self._node.server_endpoint
        return await loop.create_server(
            lambda: SocketConnectionProtocol(self._node),
            endpoint.ip_address,
            endpoint.port,
            family=socket.AF_INET,
            backlog=constants.DEFAULT_NODE_BACKLOG,
            reuse_address=True
        )

    async def _connect_to_target(
            self,
            peer_info: ConnectionPeerInfo
    ) -> None:
        logger.debug("Connecting to {}.", peer_info)
        loop = asyncio.get_running_loop()
        target_endpoint = peer_info.endpoint
        try:
            if peer_info.transport_protocol == TransportLayerProtocol.TCP:
                conn_task = loop.create_task(loop.create_connection(
                    lambda: SocketConnectionProtocol(self._node, target_endpoint),
                    target_endpoint.ip_address,
                    target_endpoint.port,
                    family=socket.AF_INET
                ))
            else:
                conn_task = loop.create_task(loop.create_datagram_endpoint(
                    lambda: SocketConnectionProtocol(self._node, target_endpoint),
                    remote_addr=(target_endpoint.ip_address, target_endpoint.port),
                    family=socket.AF_INET
                ))
            await asyncio.wait_for(conn_task, constants.CONNECTION_TIMEOUT)
        except (TimeoutError, asyncio.TimeoutError, CancelledError, ConnectionRefusedError) as e:
            logger.info("Failed to connect to: {}, {}.", peer_info, e)
            self._node.handle_connection_closed(True, peer_info)

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

    async def _perform_node_tasks(self) -> None:
        timeout = self._node.fire_alarms()
        self._node.flush_all_send_buffers()
        if timeout is None or timeout < 0:
            timeout = constants.MAX_EVENT_LOOP_TIMEOUT
        else:
            timeout = min(timeout, constants.MAX_EVENT_LOOP_TIMEOUT)
        await asyncio.sleep(timeout)
