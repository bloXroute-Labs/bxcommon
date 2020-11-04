import asyncio
from abc import ABCMeta
from typing import Dict, Callable

from bxcommon.rpc.provider.abstract_provider import SubscriptionNotification

from bxcommon.constants import LOCALHOST, WS_DEFAULT_PORT
from bxcommon.rpc.ws.ws_feed_client import WsFeedClient
from bxcommon.connections.abstract_node import AbstractNode
from bxutils import logging
from bxutils.logging.log_record_type import LogRecordType


logger = logging.get_logger(__name__)
memory_logger = logging.get_logger(LogRecordType.BxMemory, __name__)
msg_handling_logger = logging.get_logger(LogRecordType.MessageHandlingTroubleshooting, __name__)


# pylint: disable=too-many-public-methods
class AbstractFeedConnection:
    __metaclass__ = ABCMeta

    def __init__(
        self,
        node: AbstractNode,
        feed_ip: str = LOCALHOST,
        feed_port: int = WS_DEFAULT_PORT,
        extra_headers=None
    ) -> None:
        self.node = node
        self.feed_ip = feed_ip
        self.feed_port = feed_port

        self.ws_feed_client = WsFeedClient(f"ws://{self.feed_ip}:{self.feed_port}/ws", extra_headers=extra_headers)
        self.feeds_process: Dict[str, Callable[[SubscriptionNotification], None]] = {}

    async def subscribe_feeds(self) -> None:
        await self.ws_feed_client.initialize()

        for feed_name, process in self.feeds_process.items():
            self.ws_feed_client.subscribe_with_callback(process, feed_name)

        while True:
            await asyncio.sleep(0)  # otherwise program would exit
