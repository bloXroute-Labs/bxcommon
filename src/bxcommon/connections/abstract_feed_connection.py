from abc import ABCMeta
from asyncio import Task
from typing import Dict, Callable, Optional, Generic, TypeVar, Any

from bxcommon.rpc.provider.cloud_wss_provider import CloudWssProvider
from bxcommon.models.node_type import NodeType
from bxcommon.rpc.provider.abstract_provider import SubscriptionNotification

from bxcommon.constants import LOCALHOST, WS_DEFAULT_PORT
from bxcommon.rpc.provider.abstract_ws_provider import AbstractWsProvider
from bxcommon.rpc.ws.ws_client import WsClient
from bxutils import logging
from bxutils.logging.log_record_type import LogRecordType

logger = logging.get_logger(__name__)
memory_logger = logging.get_logger(LogRecordType.BxMemory, __name__)
msg_handling_logger = logging.get_logger(LogRecordType.MessageHandlingTroubleshooting, __name__)

T = TypeVar("T")


class AbstractFeedConnection(Generic[T], metaclass=ABCMeta):
    def __init__(
        self,
        node: T,
        feed_ip: str = LOCALHOST,
        feed_port: int = WS_DEFAULT_PORT,
        headers: Optional[Dict] = None,
        protocol: str = "ws"
    ) -> None:
        self.node = node
        self.feed_ip = feed_ip
        self.feed_port = feed_port

        if protocol == "ws":
            self.ws_client = WsClient(
                f"{protocol}://{self.feed_ip}:{self.feed_port}/ws",
                headers=headers,
                retry_connection=True,
                retry_callback=self._subscribe_to_feeds
            )
        else:
            self.ws_client = CloudWssProvider(
                # pyre-fixme[16]: `Variable[T]` has no attribute `opts`.
                ca_url=f"{self.node.opts.ca_cert_url}/ca_cert.pem",
                ws_uri=f"{protocol}://{self.feed_ip}:{self.feed_port}/ws",
                node_type=NodeType.BLOXROUTE_CLOUD_API.name.lower()
            )
        self.feeds_process: Dict[str, Callable[[SubscriptionNotification], None]] = {}
        self.subscription_tasks: Dict[str, Task] = {}

    async def subscribe_feeds(self, options: Optional[Dict[str, Any]] = None) -> None:
        await self.ws_client.initialize()
        await self._subscribe_to_feeds(self.ws_client, options=options)

    async def _subscribe_to_feeds(
        self, ws_client: AbstractWsProvider, options: Optional[Dict[str, Any]] = None
    ) -> None:
        for feed_name, process in self.feeds_process.items():
            if feed_name in self.subscription_tasks:
                if self.subscription_tasks[feed_name].done():
                    logger.debug("FeedConnection resubscribed to feed {} from source {}", feed_name, self.feed_ip)
                    self.subscription_tasks[feed_name] = ws_client.subscribe_with_callback(process, feed_name, options)
            else:
                logger.debug("FeedConnection subscribed to feed {} from source {}", feed_name, self.feed_ip)
                self.subscription_tasks[feed_name] = ws_client.subscribe_with_callback(process, feed_name, options)

    async def revive(self) -> None:
        if self.ws_client.ws is None or not self.ws_client.running:
            logger.info(
                "Attempting to revive websockets source feed {}:{} feeds {}...",
                self.feed_ip,
                self.feed_port,
                ", ".join(self.feeds_process.keys())
            )
            await self.ws_client.connected_event.wait()

        if self.ws_client.ws is None or not self.ws_client.running:
            await self._subscribe_to_feeds(self.ws_client)

    async def stop(self) -> None:
        for _, task in self.subscription_tasks.items():
            task.cancel()
        await self.ws_client.close()
