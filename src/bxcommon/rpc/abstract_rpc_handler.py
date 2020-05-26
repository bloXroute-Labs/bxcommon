from abc import abstractmethod, ABCMeta
from typing import Generic, TypeVar, Any, Dict, List, TYPE_CHECKING, Type

from bxcommon.rpc.json_rpc_request import JsonRpcRequest
from bxcommon.rpc.json_rpc_response import JsonRpcResponse
from bxcommon.rpc.requests.abstract_rpc_request import AbstractRpcRequest
from bxcommon.rpc.rpc_errors import RpcParseError, RpcError, RpcInternalError
from bxcommon.rpc.rpc_request_type import RpcRequestType

if TYPE_CHECKING:
    # noinspection PyUnresolvedReferences
    # pylint: disable=ungrouped-imports,cyclic-import
    from bxcommon.connections.abstract_node import AbstractNode

Node = TypeVar("Node", bound="AbstractNode")
Req = TypeVar("Req")
Res = TypeVar("Res")


class AbstractRpcHandler(Generic[Node, Req, Res], metaclass=ABCMeta):
    node: Node
    request_handlers: Dict[RpcRequestType, Type[AbstractRpcRequest[Node]]]

    def __init__(self, node: Node) -> None:
        self.node = node
        self.request_handlers = {}

    async def handle_request(self, request: Req) -> Res:
        try:
            payload = await self.parse_request(request)
        except Exception:
            raise RpcParseError()

        rpc_request = JsonRpcRequest.from_json(payload)
        request_handler = self.get_request_handler(rpc_request)
        try:
            return self.serialize_response(
                await request_handler.process_request()
            )
        except RpcError as e:
            raise e
        except Exception as e:
            raise RpcInternalError(rpc_request.id, str(e))

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
    def get_request_handler(self, request: JsonRpcRequest) -> AbstractRpcRequest:
        pass

    @abstractmethod
    def serialize_response(self, response: JsonRpcResponse) -> Res:
        pass
