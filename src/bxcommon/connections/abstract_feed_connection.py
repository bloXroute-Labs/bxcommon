from abc import ABCMeta
from asyncio import Task
from typing import Dict, Callable, Optional, Generic, TypeVar

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
        headers: Optional[Dict] = None
    ) -> None:
        self.node = node
        self.feed_ip = feed_ip
        self.feed_port = feed_port

        self.ws_client = WsClient(
            f"ws://{self.feed_ip}:{self.feed_port}/ws",
            headers=headers,
            retry_connection=True,
            retry_callback=self._subscribe_to_feeds
        )
        self.feeds_process: Dict[str, Callable[[SubscriptionNotification], None]] = {}
        self.subscription_task: Optional[Task] = None

    async def subscribe_feeds(self) -> None:
        await self.ws_client.initialize()
        await self._subscribe_to_feeds(self.ws_client)

    async def _subscribe_to_feeds(self, ws_client: AbstractWsProvider) -> None:
        subscription_task = self.subscription_task
        if subscription_task is not None:
            subscription_task.cancel()

        for feed_name, process in self.feeds_process.items():
            logger.debug("FeedConnection subscribed to feed {} from source {}", feed_name, self.feed_ip)
            self.subscription_task = ws_client.subscribe_with_callback(process, feed_name)

    async def revive(self) -> None:
        if self.ws_client.ws is None or not self.ws_client.running:
            logger.info("Attempting to revive websockets source feed...")
            await self.ws_client.reconnect()
            await self.subscribe_feeds()

    async def stop(self) -> None:
        await self.ws_client.close()
