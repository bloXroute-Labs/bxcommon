import json
from typing import Any, Optional, Dict

from bxcommon.rpc import rpc_constants
from bxcommon.rpc.rpc_errors import RpcError
from bxcommon.utils import json_utils


class JsonRpcResponse:
    id: Optional[str]
    result: Optional[Any]
    error: Optional[RpcError]

    def __init__(
        self,
        request_id: Optional[str],
        result: Optional[Any] = None,
        error: Optional[RpcError] = None,
    ) -> None:
        if result is not None and error is not None:
            raise ValueError(
                "Cannot instantiate a JsonRpcResponse with both an error and a result!"
            )

        self.id = request_id
        self.result = result
        self.error = error
        self.json_rpc_version = rpc_constants.JSON_RPC_VERSION

    def __str__(self) -> str:
        return f"JsonRpcResponse<{self.to_jsons()}>"

    def to_json(self) -> Dict[str, Any]:
        fields = {
            rpc_constants.JSON_RPC_VERSION_FIELD: self.json_rpc_version,
            rpc_constants.JSON_RPC_REQUEST_ID: self.id,
        }
        result = self.result
        if result is not None:
            fields[rpc_constants.JSON_RPC_RESULT] = result

        error = self.error
        if error is not None:
            fields[rpc_constants.JSON_RPC_ERROR] = error.to_json()
        return fields

    def to_jsons(self) -> str:
        return json_utils.serialize(self.to_json())

    @classmethod
    def from_json(cls, payload: Dict[str, Any]) -> "JsonRpcResponse":
        return cls(
            payload.get(rpc_constants.JSON_RPC_REQUEST_ID, None),
            payload.get(rpc_constants.JSON_RPC_RESULT, None),
            payload.get(rpc_constants.JSON_RPC_ERROR, None)
        )

    @classmethod
    def from_jsons(cls, payload: str) -> "JsonRpcResponse":
        return cls.from_json(json.loads(payload))
