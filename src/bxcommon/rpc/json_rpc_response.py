import json
from typing import Any, Optional, Dict, Union

import humps

from bxcommon.rpc import rpc_constants
from bxcommon.rpc.rpc_errors import RpcError
from bxutils.encoding import json_encoder
from bxutils import utils
from bxutils.encoding.json_encoder import Case


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
        if (result is not None) and (error is not None):
            raise ValueError(
                "Cannot instantiate a JsonRpcResponse with both an error and a result."
            )

        self.id = request_id
        self.result = result
        self.error = error
        self.json_rpc_version = rpc_constants.JSON_RPC_VERSION

    def __str__(self) -> str:
        return f"JsonRpcResponse<{self.to_jsons()}>"

    def __eq__(self, o: object) -> bool:
        if isinstance(o, JsonRpcResponse):
            return (
                self.id == o.id
                and self.result == o.result
                and self.error == o.error
                and self.json_rpc_version == o.json_rpc_version
            )
        else:
            return False

    def to_json(self, case: Case = Case.SNAKE) -> Dict[str, Any]:
        fields = {
            rpc_constants.JSON_RPC_VERSION_FIELD: self.json_rpc_version,
            rpc_constants.JSON_RPC_REQUEST_ID: self.id,
        }
        result = self.result
        if result is not None:
            if case == Case.CAMEL and isinstance(result, dict):
                fields[rpc_constants.JSON_RPC_RESULT] = humps.camelize(
                    result
                )
            else:
                fields[rpc_constants.JSON_RPC_RESULT] = result

        error = self.error
        if error is not None:
            fields[rpc_constants.JSON_RPC_ERROR] = error.to_json()
        return fields

    def to_jsons(self, case: Case = Case.SNAKE) -> str:
        return json_encoder.to_json(self.to_json(case))

    @classmethod
    def from_json(cls, payload: Dict[str, Any]) -> "JsonRpcResponse":
        if not (rpc_constants.JSON_RPC_RESULT not in payload) ^ (rpc_constants.JSON_RPC_ERROR not in payload):
            raise ValueError(
                "Cannot instantiate a message with neither (or both) a result and error."
            )
        return cls(
            payload.get(rpc_constants.JSON_RPC_REQUEST_ID, None),
            payload.get(rpc_constants.JSON_RPC_RESULT, None),
            utils.optional_map(
                payload.get(rpc_constants.JSON_RPC_ERROR, None),
                RpcError.from_json
            )
        )

    @classmethod
    def from_jsons(cls, payload: Union[bytes, str]) -> "JsonRpcResponse":
        return cls.from_json(json.loads(payload))
