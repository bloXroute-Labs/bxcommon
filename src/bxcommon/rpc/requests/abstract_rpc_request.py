import json
from abc import ABCMeta
from typing import Union, Dict, List, Any, Type, TYPE_CHECKING

from aiohttp.web_exceptions import HTTPException, HTTPOk
from aiohttp.web import Response

from bxcommon.rpc.rpc_request_type import RpcRequestType

if TYPE_CHECKING:
    # noinspection PyUnresolvedReferences
    # pylint: disable=ungrouped-imports,cyclic-import
    from bxcommon.connections.abstract_node import AbstractNode


class AbstractRpcRequest(metaclass=ABCMeta):
    method: RpcRequestType
    request_id: str
    params: Union[Dict[str, Any], List[Any], None]
    help: Dict[str, Any]

    def __init__(
            self,
            method: RpcRequestType,
            node: "AbstractNode",
            request_id: str = "",
            params: Union[Dict[str, Any], List[Any], None] = None
    ):
        self.method = method
        self.request_id = request_id
        if params is not None and isinstance(params, dict):
            params = {k.lower(): v for k, v in params.items()}
        self.params = params
        self._node = node
        self.help = {}

    async def process_request(self) -> Response:
        pass

    def _format_response(
            self, result: Union[str, Dict[str, Any], List[Any]], response_type: Type[HTTPException] = HTTPOk
    ) -> Response:
        request_id = self.request_id
        response_json = {
            "result": result,
            "error": None,
            "code": response_type.status_code,
            "message": "",
            "id": request_id
        }
        return response_type(text=json.dumps(response_json))
