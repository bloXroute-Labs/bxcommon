import json
import asyncio
from asyncio import Future
from typing import TYPE_CHECKING, Dict, NamedTuple, Optional, Any

from bxcommon.rpc.abstract_rpc_handler import AbstractRpcHandler
from bxcommon.rpc.bx_json_rpc_request import BxJsonRpcRequest
from bxcommon.rpc.json_rpc_response import JsonRpcResponse
from bxcommon.rpc.requests.abstract_rpc_request import AbstractRpcRequest
from bxcommon.rpc.requests.subscribe_rpc_request import SubscribeRpcRequest
from bxcommon.rpc.requests.unsubscribe_rpc_request import UnsubscribeRpcRequest
from bxcommon.rpc.rpc_errors import RpcParseError, RpcError, RpcInternalError
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
    feed_name: str
    task: Future


class AbstractWsRpcHandler(AbstractRpcHandler["AbstractNode", str, str]):
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

    async def handle_request(self, request: str) -> str:
        try:
            payload = await self.parse_request(request)
        except Exception:
            raise RpcParseError(None, f"Unable to parse the request: {request}")

        rpc_request = BxJsonRpcRequest.from_json(payload)

        request_handler = self.get_request_handler(rpc_request)
        try:
            return self.serialize_response(
                await request_handler.process_request()
            )
        except RpcError as e:
            raise e
        except Exception as e:
            logger.error(
                log_messages.INTERNAL_ERROR_HANDLING_RPC_REQUEST, e, rpc_request
            )
            raise RpcInternalError(rpc_request.id, "Please contact bloXroute support.")

    async def parse_request(self, request: str) -> Dict[str, Any]:
        return json.loads(request)

    def get_request_handler(self, request: BxJsonRpcRequest) -> AbstractRpcRequest:
        if request.method == RpcRequestType.SUBSCRIBE and request.method in self.request_handlers:
            return self._subscribe_request_factory(request, self.node)
        elif request.method == RpcRequestType.UNSUBSCRIBE and request.method in self.request_handlers:
            return self._unsubscribe_request_factory(request, self.node)

        request_handler_type = self.request_handlers[request.method]
        # seems to be pyre bug: https://github.com/facebook/pyre-check/issues/267
        # pyre-fixme[45]: Cannot instantiate abstract class `Abstract` with abstract method `run`.
        return request_handler_type(request, self.node)

    def serialize_response(self, response: JsonRpcResponse) -> str:
        return response.to_jsons(self.case)

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
        for subscription_id in self.subscriptions:
            feed_name = self._on_unsubscribe(subscription_id)
            assert feed_name is not None
            self.feed_manager.unsubscribe_from_feed(feed_name, subscription_id)
        self.subscriptions = {}

        self.disconnect_event.set()

    def _on_new_subscriber(self, subscriber: Subscriber, feed_name: str) -> None:
        task = asyncio.ensure_future(self.handle_subscription(subscriber))
        self.subscriptions[subscriber.subscription_id] = Subscription(
            subscriber, feed_name, task
        )
        self.node.on_new_subscriber_request()

    def _on_unsubscribe(self, subscriber_id: str) -> Optional[str]:
        if subscriber_id in self.subscriptions:
            (_, feed_name, task) = self.subscriptions.pop(subscriber_id)
            task.cancel()
            return feed_name
        return None

    def _subscribe_request_factory(
        self, request: BxJsonRpcRequest, node: "AbstractNode"
    ) -> AbstractRpcRequest:
        return SubscribeRpcRequest(
            request, node, self.feed_manager, self._on_new_subscriber
        )

    def _unsubscribe_request_factory(
        self, request: BxJsonRpcRequest, node: "AbstractNode"
    ) -> AbstractRpcRequest:
        return UnsubscribeRpcRequest(
            request, node, self.feed_manager, self._on_unsubscribe
        )