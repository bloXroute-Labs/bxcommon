from typing import Union, Any, Dict, List, Type, TYPE_CHECKING
from json.decoder import JSONDecodeError
from aiohttp.web import Request, Response
from aiohttp.web_exceptions import HTTPBadRequest

from bxcommon.rpc import rpc_constants
from bxcommon.rpc.requests.blxr_transaction_rpc_request import BlxrTransactionRpcRequest
from bxcommon.rpc.requests.abstract_rpc_request import AbstractRpcRequest
from bxcommon.rpc.rpc_request_type import RpcRequestType
from bxutils import logging

if TYPE_CHECKING:
    # noinspection PyUnresolvedReferences
    # pylint: disable=ungrouped-imports,cyclic-import
    from bxcommon.connections.abstract_node import AbstractNode


logger = logging.get_logger(__name__)


class RpcRequestHandler:

    CONTENT_TYPE: str = rpc_constants.CONTENT_TYPE_HEADER_KEY
    PLAIN: str = rpc_constants.PLAIN_HEADER_TYPE
    REQUEST_ID: str = "id"
    REQUEST_METHOD: str = "method"
    REQUEST_PARAMS: str = "params"
    request_id: str
    _node: "AbstractNode"

    def __init__(self, node):
        self._node = node
        self._request_handlers: Dict[RpcRequestType, Type[AbstractRpcRequest]] = {
            RpcRequestType.BLXR_TX: BlxrTransactionRpcRequest,
        }
        self.request_id = ""

    async def handle_request(self, request: Request) -> Response:
        self.request_id = ""
        try:
            # pyre-ignore
            content_type = request.headers[self.CONTENT_TYPE]
        except KeyError:
            raise HTTPBadRequest(text=f"Request must have a {self.CONTENT_TYPE} header!")
        if content_type != self.PLAIN:
            raise HTTPBadRequest(text=f"{self.CONTENT_TYPE} must be {self.PLAIN}, not {content_type}!")
        try:
            payload = await request.json()
        except JSONDecodeError:
            body = await request.text()
            raise HTTPBadRequest(text=f"Request body: {body}, is not JSON serializable!")
        method = None
        try:
            method = payload[self.REQUEST_METHOD]
            method = RpcRequestType[method.upper()]
        except KeyError:
            # pyre-ignore
            if method is None:
                raise HTTPBadRequest(text=f"RPC request does not contain a method!")

            possible_values = [rpc_type.lower() for rpc_type in RpcRequestType.__members__.keys()]
            raise HTTPBadRequest(
                text=f"RPC method: {method} is not recognized (possible_values: {possible_values})."
            )
        self.request_id = payload.get(self.REQUEST_ID, "")
        request_params = payload.get(self.REQUEST_PARAMS, None)
        rpc_request = self._get_rpc_request(method, request_params)
        return await rpc_request.process_request()

    async def help(self) -> List[Any]:
        return [
            {
                "method": method.name.lower(),
                "id": "Optional - [unique request identifier string].",
                "params": self._request_handlers[method].help["params"],
                "description": self._request_handlers[method].help.get("description"),
            }
            for method in self._request_handlers
        ]

    def _get_rpc_request(
            self,
            method: RpcRequestType,
            request_params: Union[Dict[str, Any], List[Any], None]
    ) -> AbstractRpcRequest:
        return self._request_handlers[method](method, self._node, self.request_id, request_params)
