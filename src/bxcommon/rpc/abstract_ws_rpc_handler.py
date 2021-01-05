import json
import asyncio
from asyncio import Future
from typing import TYPE_CHECKING, Dict, NamedTuple, Optional, Any, cast, Type

from aiohttp import WSMessage
from multidict import CIMultiDictProxy

from bxcommon.feed.feed import FeedKey
from bxcommon.rpc.abstract_rpc_handler import AbstractRpcHandler
from bxcommon.rpc.bx_json_rpc_request import BxJsonRpcRequest
from bxcommon.rpc.json_rpc_response import JsonRpcResponse
from bxcommon.rpc.requests.abstract_rpc_request import AbstractRpcRequest
from bxcommon.rpc.requests.subscribe_rpc_request import SubscribeRpcRequest
from bxcommon.rpc.requests.unsubscribe_rpc_request import UnsubscribeRpcRequest
from bxcommon.rpc.rpc_errors import RpcParseError
from bxcommon.rpc.rpc_request_type import RpcRequestType

from bxcommon import constants
from bxcommon.feed.feed_manager import FeedManager
from bxcommon.feed.subscriber import Subscriber
from bxutils import log_messages
from bxutils import logging
from bxutils.encoding.json_encoder import Case

if TYPE_CHECKING:
    # noinspection PyUnresolvedReferences
    # pylint: disable=ungrouped-imports,cyclic-import
    from bxcommon.connections.abstract_node import AbstractNode


logger = logging.get_logger(__name__)


class Subscription(NamedTuple):
    subscriber: Subscriber
    feed_key: FeedKey
    task: Future


class WsRequest(NamedTuple):
    message: WSMessage
    headers: CIMultiDictProxy


class AbstractWsRpcHandler(AbstractRpcHandler["AbstractNode", WsRequest, str]):
    feed_manager: FeedManager
    subscriptions: Dict[str, Subscription]
    subscribed_messages: "asyncio.Queue[BxJsonRpcRequest]"

    def __init__(self, node: "AbstractNode", feed_manager: FeedManager, case: Case) -> None:
        super().__init__(node, case)
        self.subscriptions = {}

        self.feed_manager = feed_manager
        self.subscribed_messages = asyncio.Queue(
            constants.RPC_SUBSCRIBER_MAX_QUEUE_SIZE
        )
        self.disconnect_event = asyncio.Event()

    async def parse_request(self, request: WsRequest) -> Dict[str, Any]:
        try:
            request_message_dict = {}
            if request.message.data:
                request_message_dict = json.loads(request.message.data)
            assert isinstance(request_message_dict, Dict)
            return request_message_dict
        except Exception:
            raise RpcParseError(None, f"Unable to parse the request: {request}")

    def get_request_handler(self, request: BxJsonRpcRequest) -> AbstractRpcRequest:
        if request.method == RpcRequestType.SUBSCRIBE and request.method in self.request_handlers:
            return self._subscribe_request_factory(request)
        elif request.method == RpcRequestType.UNSUBSCRIBE and request.method in self.request_handlers:
            return self._unsubscribe_request_factory(request)

        request_handler_type = self.request_handlers[request.method]
        # seems to be pyre bug: https://github.com/facebook/pyre-check/issues/267
        # pyre-fixme[45]: Cannot instantiate abstract class `Abstract` with abstract method `run`.
        return request_handler_type(request, self.node)

    def serialize_response(self, response: JsonRpcResponse) -> str:
        return response.to_jsons(self.case)

    def serialize_cached_subscription_message(self, message: BxJsonRpcRequest) -> bytes:
        return self.node.serialized_message_cache.serialize_from_cache(message, self.case)

    async def get_next_subscribed_message(self) -> BxJsonRpcRequest:
        return await self.subscribed_messages.get()

    async def handle_subscription(self, subscriber: Subscriber) -> None:
        while True:
            notification = await subscriber.receive()
            # subscription notifications are sent as JSONRPC requests
            next_message = BxJsonRpcRequest(
                None,
                RpcRequestType.SUBSCRIBE,
                {
                    "subscription": subscriber.subscription_id,
                    "result": notification
                }
            )
            if self.subscribed_messages.full():
                logger.error(
                    log_messages.BAD_RPC_SUBSCRIBER,
                    self.subscribed_messages.qsize(),
                    list(self.subscriptions.keys())
                )
                asyncio.create_task(self.async_close())
                return
            else:
                await self.subscribed_messages.put(next_message)

    async def wait_for_close(self) -> None:
        await self.disconnect_event.wait()

    async def async_close(self) -> None:
        self.close()

    def close(self) -> None:
        subscription_ids = list(self.subscriptions.keys())
        for subscription_id in subscription_ids:
            feed_key = self._on_unsubscribe(subscription_id)
            assert feed_key is not None
            self.feed_manager.unsubscribe_from_feed(feed_key, subscription_id)
        self.subscriptions = {}

        self.disconnect_event.set()

    def _on_new_subscriber(self, subscriber: Subscriber, feed_key: FeedKey) -> None:
        task = asyncio.ensure_future(self.handle_subscription(subscriber))
        self.subscriptions[subscriber.subscription_id] = Subscription(
            subscriber, feed_key, task
        )
        self.node.on_new_subscriber_request()

    def _on_unsubscribe(self, subscriber_id: str) -> Optional[FeedKey]:
        if subscriber_id in self.subscriptions:
            (_, feed_key, task) = self.subscriptions.pop(subscriber_id)
            task.cancel()
            return feed_key
        return None

    def _subscribe_request_factory(
        self, request: BxJsonRpcRequest
    ) -> AbstractRpcRequest:
        subscribe_rpc_request = cast(Type[SubscribeRpcRequest], self.request_handlers[RpcRequestType.SUBSCRIBE])
        return subscribe_rpc_request(
            request, self.node, self.feed_manager, self._on_new_subscriber
        )

    def _unsubscribe_request_factory(
        self, request: BxJsonRpcRequest
    ) -> AbstractRpcRequest:
        unsubscribe_rpc_request = cast(Type[UnsubscribeRpcRequest], self.request_handlers[RpcRequestType.UNSUBSCRIBE])
        return unsubscribe_rpc_request(
            request, self.node, self.feed_manager, self._on_unsubscribe
        )
