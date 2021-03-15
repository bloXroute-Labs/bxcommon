from abc import abstractmethod
from typing import Union, Dict, List, Any, TYPE_CHECKING, Optional, TypeVar, Generic

from bxcommon.rpc import rpc_constants
from bxcommon.rpc.bx_json_rpc_request import BxJsonRpcRequest
from bxcommon.rpc.json_rpc_response import JsonRpcResponse
from bxcommon.rpc.rpc_errors import RpcInvalidParams
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
        self.account_cache_key = request.account_cache_key
        self.method = request.method
        self.request_id = request.id
        params = request.params
        if params is not None and isinstance(params, dict):
            params = {k.lower(): v for k, v in params.items()}
        self.params = params
        self.node = node
        self.help = {}
        self.headers = request.account_cache_key

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

    def authenticate_request(self) -> None:
        params = self.params
        if params is not None:
            assert isinstance(params, dict)
            rpc_server = self.node.rpc_server
            if (
                params is not None
                and rpc_constants.AUTHORIZATION_HEADER_KEY in params
                and rpc_server is not None
            ):
                request_auth_key = params[rpc_constants.AUTHORIZATION_HEADER_KEY]
                assert rpc_server is not None
                if rpc_server.encoded_auth != request_auth_key:
                    raise RpcInvalidParams(None, f"Authorization header {request_auth_key} is invalid.")
