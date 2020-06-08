from typing import List, Any, Union, Dict, Optional

from bxcommon.rpc import rpc_constants
from bxcommon.rpc.json_rpc_request import JsonRpcRequest
from bxcommon.rpc.rpc_errors import RpcMethodNotFound
from bxcommon.rpc.rpc_request_type import RpcRequestType


class BxJsonRpcRequest(JsonRpcRequest):
    method: RpcRequestType

    def __init__(
        self,
        request_id: Optional[str],
        method: RpcRequestType,
        params: Union[List[Any], Dict[Any, Any], None],
    ) -> None:
        super().__init__(request_id, method.name.lower(), params)
        self.method = method

    def __str__(self):
        return f"BxJsonRpcRequest<{self.to_json()}>"

    def to_json(self) -> Dict[str, Any]:
        return {
            rpc_constants.JSON_RPC_VERSION_FIELD: self.json_rpc_version,
            rpc_constants.JSON_RPC_REQUEST_ID: self.id,
            rpc_constants.JSON_RPC_METHOD: self.method.name.lower(),
            rpc_constants.JSON_RPC_PARAMS: self.params,
        }

    @classmethod
    def from_json(cls, payload: Dict[str, Any]) -> "BxJsonRpcRequest":
        request_id = payload.get(rpc_constants.JSON_RPC_REQUEST_ID, None)
        if rpc_constants.JSON_RPC_METHOD not in payload:
            raise RpcMethodNotFound(request_id, "RPC request does not contain a method.")

        str_method = payload[rpc_constants.JSON_RPC_METHOD]
        try:
            method = RpcRequestType[str_method.upper()]
        except KeyError:
            possible_values = [rpc_type.lower() for rpc_type in RpcRequestType.__members__.keys()]
            raise RpcMethodNotFound(
                request_id,
                f"RPC method: {str_method} is not recognized (possible_values: {possible_values}).",
            )
        request_params = payload.get(rpc_constants.JSON_RPC_PARAMS, None)
        return cls(request_id, method, request_params)
