import json
from typing import List, Any, Union, Dict, Optional

from bxcommon.rpc import rpc_constants
from bxcommon.rpc.rpc_errors import RpcMethodNotFound
from bxutils.encoding import json_encoder


class JsonRpcRequest:
    id: Optional[str]
    method_name: str
    params: Union[List[Any], Dict[Any, Any], None]

    def __init__(
        self,
        request_id: Optional[str],
        method: str,
        params: Union[List[Any], Dict[Any, Any], None],
    ) -> None:
        self.id = request_id
        self.method_name = method
        self.params = params
        self.json_rpc_version = rpc_constants.JSON_RPC_VERSION

    def __str__(self):
        return f"JsonRpcRequest<{self.to_json()}>"

    def __eq__(self, o: object) -> bool:
        if isinstance(o, JsonRpcRequest):
            return (
                self.id == o.id
                and self.method_name == o.method_name
                and self.params == o.params
                and self.json_rpc_version == o.json_rpc_version
            )
        else:
            return False

    def to_json(self) -> Dict[str, Any]:
        return {
            rpc_constants.JSON_RPC_VERSION_FIELD: self.json_rpc_version,
            rpc_constants.JSON_RPC_REQUEST_ID: self.id,
            rpc_constants.JSON_RPC_METHOD: self.method_name,
            rpc_constants.JSON_RPC_PARAMS: self.params,
        }

    def to_jsons(self) -> str:
        return json_encoder.to_json(self.to_json())

    @classmethod
    def from_json(cls, payload: Dict[str, Any]) -> "JsonRpcRequest":
        request_id = payload.get(rpc_constants.JSON_RPC_REQUEST_ID, None)
        if rpc_constants.JSON_RPC_METHOD not in payload:
            raise RpcMethodNotFound(request_id, "RPC request does not contain a method.")

        method = payload[rpc_constants.JSON_RPC_METHOD]
        request_params = payload.get(rpc_constants.JSON_RPC_PARAMS, None)
        return cls(request_id, method, request_params)

    @classmethod
    def from_jsons(cls, payload: Union[bytes, str]) -> "JsonRpcRequest":
        return cls.from_json(json.loads(payload))
