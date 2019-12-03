import asyncio
import socket
from asyncio import CancelledError
from asyncio.events import AbstractServer
from typing import Iterator, Tuple, List, Coroutine, Generator

from bxcommon import constants
from bxcommon.connections.abstract_node import AbstractNode
from bxcommon.network.ip_endpoint import IpEndpoint
from bxcommon.network.socket_connection_protocol import SocketConnectionProtocol
from bxcommon.network.transport_layer_protocol import TransportLayerProtocol
from bxutils import logging

logger = logging.get_logger(__name__)


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
        async with node_server:
            await self._connect_to_peers()
            timeout = self._node.fire_alarms()
            self._started.set_result(True)
            while not self._stop_requested:
                if timeout is None or timeout < 0:
                    timeout = constants.MAX_EVENT_LOOP_TIMEOUT
                else:
                    timeout = min(timeout, constants.MAX_EVENT_LOOP_TIMEOUT)
                if self._node.force_exit():
                    self.stop()
                    logger.info("Ending event loop. Shutdown has been requested manually.")
                    break
                self._node.flush_all_send_buffers()
                await self._process_new_connections_requests()
                await asyncio.sleep(timeout)
                timeout = self._node.fire_alarms()

    async def _process_new_connections_requests(self):
        address = self._node.pop_next_connection_address()
        peers_info = []
        while address is not None:
            peers_info.append((IpEndpoint(*address), TransportLayerProtocol.TCP))
            address = self._node.pop_next_connection_address()
        if peers_info:
            await asyncio.gather(*self._gather_connections(iter(peers_info)))

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
            target_endpoint: IpEndpoint,
            protocol: int = TransportLayerProtocol.TCP
    ) -> None:
        logger.debug("Connecting to {}.", target_endpoint)
        loop = asyncio.get_running_loop()
        try:
            if protocol == TransportLayerProtocol.TCP:
                await loop.create_connection(
                    lambda: SocketConnectionProtocol(self._node, target_endpoint),
                    target_endpoint.ip_address,
                    target_endpoint.port,
                    family=socket.AF_INET
                )
            else:
                await loop.create_datagram_endpoint(
                    lambda: SocketConnectionProtocol(self._node, target_endpoint),
                    remote_addr=(target_endpoint.ip_address, target_endpoint.port),
                    family=socket.AF_INET
                )
        except (TimeoutError, asyncio.TimeoutError, CancelledError, ConnectionRefusedError) as e:
            logger.error("Failed to connect to target {}, {}.", target_endpoint, e, exc_info=True)
            # TODO : add a retries mechanism here.

    def _iter_outbound_peers(self) -> Generator[Tuple[IpEndpoint, int], None, None]:
        sdn_address = self._node.get_sdn_address()
        if sdn_address:
            yield IpEndpoint(*sdn_address), TransportLayerProtocol.TCP
        else:
            logger.debug("SDN address not provided, skipping connection. This is expected for gateways.")
        for peer_info in self._node.get_outbound_peer_addresses():
            if len(peer_info) > 2:
                protocol = peer_info[2]
            else:
                protocol = TransportLayerProtocol.TCP
            yield IpEndpoint(*peer_info[:2]), protocol

    def _gather_connections(
            self, connections_info: Iterator[Tuple[IpEndpoint, int]]
    ) -> List[Coroutine]:
        return [
            self._connect_to_target(endpoint, protocol) for endpoint, protocol in connections_info
        ]
