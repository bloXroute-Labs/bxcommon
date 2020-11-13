from abc import abstractmethod
from typing import Generic, TypeVar, Any, Dict, List, TYPE_CHECKING, Type
import base64

from bxcommon import constants
from bxcommon.rpc import rpc_constants
from bxcommon.rpc.bx_json_rpc_request import BxJsonRpcRequest
from bxcommon.rpc.json_rpc_response import JsonRpcResponse
from bxcommon.rpc.requests.abstract_rpc_request import AbstractRpcRequest
from bxcommon.rpc.rpc_errors import RpcParseError, RpcError, RpcInternalError
from bxcommon.rpc.rpc_request_type import RpcRequestType
from bxutils import logging, log_messages
from bxutils.encoding.json_encoder import Case

logger = logging.get_logger(__name__)

if TYPE_CHECKING:
    # noinspection PyUnresolvedReferences
    # pylint: disable=ungrouped-imports,cyclic-import
    from bxcommon.connections.abstract_node import AbstractNode

Node = TypeVar("Node", bound="AbstractNode")
Req = TypeVar("Req")
Res = TypeVar("Res")


class AbstractRpcHandler(Generic[Node, Req, Res]):
    node: Node
    request_handlers: Dict[RpcRequestType, Type[AbstractRpcRequest[Node]]]
    case: Case

    def __init__(self, node: Node, case: Case = Case.SNAKE) -> None:
        self.node = node
        self.request_handlers = {}
        self.case = case

    async def handle_request(self, request: Req) -> Res:
        try:
            payload = await self.parse_request(request)
        except Exception:
            raise RpcParseError(None, f"Unable to parse the request: {request}")

        rpc_request = BxJsonRpcRequest.from_json(payload)

        # request can be many types, not all of them have "headers"
        headers = getattr(request, "headers", None)
        if headers and rpc_constants.AUTHORIZATION_HEADER_KEY in headers:
            request_auth_key = headers[rpc_constants.AUTHORIZATION_HEADER_KEY]
            account_cache_key = base64.b64decode(request_auth_key).decode(constants.DEFAULT_TEXT_ENCODING)
            rpc_request.account_cache_key = account_cache_key

        request_handler = self.get_request_handler(rpc_request)
        try:
            return self.serialize_response(
                await request_handler.process_request()
            )
        except RpcError as e:
            raise e
        except Exception as e:
            logger.exception(
                log_messages.INTERNAL_ERROR_HANDLING_RPC_REQUEST, e, rpc_request
            )
            raise RpcInternalError(rpc_request.id, "Please contact bloXroute support.")

    async def help(self) -> List[Any]:
        return [
            {
                "method": method.name.lower(),
                "id": "Optional - [unique request identifier string].",
                "params": self.request_handlers[method].help["params"],
                "description": self.request_handlers[method].help["description"],
            }
            for method in self.request_handlers
        ]

    @abstractmethod
    async def parse_request(self, request: Req) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_request_handler(self, request: BxJsonRpcRequest) -> AbstractRpcRequest:
        pass

    @abstractmethod
    def serialize_response(self, response: JsonRpcResponse) -> Res:
        pass
