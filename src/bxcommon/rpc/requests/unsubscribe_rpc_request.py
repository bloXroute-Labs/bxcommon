from typing import TYPE_CHECKING, Callable, Optional

from bxcommon.feed.feed import FeedKey
from bxcommon.rpc.bx_json_rpc_request import BxJsonRpcRequest
from bxcommon.rpc.json_rpc_response import JsonRpcResponse
from bxcommon.rpc.requests.abstract_rpc_request import AbstractRpcRequest
from bxcommon.rpc.rpc_errors import RpcInvalidParams
from bxcommon.feed.feed_manager import FeedManager

if TYPE_CHECKING:
    # noinspection PyUnresolvedReferences
    # pylint: disable=ungrouped-imports,cyclic-import
    from bxcommon.connections.abstract_node import AbstractNode


class UnsubscribeRpcRequest(AbstractRpcRequest["AbstractNode"]):
    help = {
        "params": "[subscription_id]: Subscription ID returned from subscribe call",
        "description": "Unsubscribe from provided subscription ID"
    }

    def __init__(
        self,
        request: BxJsonRpcRequest,
        node: "AbstractNode",
        feed_manager: FeedManager,
        unsubscribe_handler: Callable[[str], Optional[FeedKey]]
    ) -> None:
        self.feed_manager = feed_manager
        self.unsubscribe_handler = unsubscribe_handler
        self.subscriber_id = ""
        super().__init__(request, node)
        assert self.subscriber_id != ""

    def validate_params(self) -> None:
        params = self.params
        if (
            not isinstance(params, list)
            or len(params) != 1
            or not isinstance(params[0], str)
        ):
            raise RpcInvalidParams(
                self.request_id,
                "Unsubscribe RPC request params must be a list of length 1."
            )
        self.subscriber_id = params[0]

    async def process_request(self) -> JsonRpcResponse:
        feed_key = self.unsubscribe_handler(self.subscriber_id)
        if feed_key is None:
            raise RpcInvalidParams(
                self.request_id,
                f"Subscriber {self.subscriber_id} was not found."
            )
        self.feed_manager.unsubscribe_from_feed(feed_key, self.subscriber_id)
        return JsonRpcResponse(self.request_id, True)
