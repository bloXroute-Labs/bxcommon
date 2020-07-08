from abc import abstractmethod
from typing import Union, Dict, List, Any, TYPE_CHECKING, Optional, TypeVar, Generic

from bxcommon.rpc.bx_json_rpc_request import BxJsonRpcRequest
from bxcommon.rpc.json_rpc_response import JsonRpcResponse
from bxcommon.rpc.rpc_request_type import RpcRequestType

if TYPE_CHECKING:
    # noinspection PyUnresolvedReferences
    # pylint: disable=ungrouped-imports,cyclic-import
    from bxcommon.connections.abstract_node import AbstractNode

Node = TypeVar("Node", bound="AbstractNode")


class AbstractRpcRequest(Generic[Node]):
    method: RpcRequestType
    request_id: Optional[str]
    params: Union[Dict[str, Any], List[Any], None]
    node: Node
    help: Dict[str, Any]

    def __init__(
        self,
        request: BxJsonRpcRequest,
        node: Node,
    ) -> None:
        self.method = request.method
        self.request_id = request.id
        params = request.params
        if params is not None and isinstance(params, dict):
            params = {k.lower(): v for k, v in params.items()}
        self.params = params
        self.node = node
        self.help = {}

        self.validate_params()

    @abstractmethod
    def validate_params(self) -> None:
        pass

    @abstractmethod
    async def process_request(self) -> JsonRpcResponse:
        pass

    def ok(self, result: Optional[Any]) -> JsonRpcResponse:
        return JsonRpcResponse(
            self.request_id,
            result
        )
