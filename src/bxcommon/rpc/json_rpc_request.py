import json
from typing import List, Any, Union, Dict, Optional, Tuple

import humps
import orjson

from bxcommon.rpc import rpc_constants
from bxcommon.rpc.rpc_errors import RpcMethodNotFound
from bxutils.encoding import json_encoder
from bxutils.encoding.json_encoder import Case


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

    def __str__(self) -> str:
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

    def to_json(self, case: Case = Case.SNAKE) -> Dict[str, Any]:
        params = self.params
        if params is not None and case == Case.CAMEL:
            params = humps.camelize(params)

        return {
            rpc_constants.JSON_RPC_VERSION_FIELD: self.json_rpc_version,
            rpc_constants.JSON_RPC_REQUEST_ID: self.id,
            rpc_constants.JSON_RPC_METHOD: self.method_name,
            rpc_constants.JSON_RPC_PARAMS: params,
        }

    def to_jsons(self, case: Case = Case.SNAKE) -> str:
        json_dict = self.to_json(case)
        return json_encoder.to_json(json_dict)

    def to_json_bytes(self, case: Case = Case.SNAKE) -> bytes:
        json_dict = self.to_json(case)
        return orjson.dumps(json_dict)

    def to_json_bytes_split_serialization(self, case: Case) -> Tuple[bytes, str]:
        """
        This method should only be called for subscription messages.

        No runtime checks are added for performance reasons, so please make sure
        that other RPC request types don't trigger this.

        Returns result serialized separately for caching later.
        """
        json_dict = self.to_json(case)
        result = orjson.dumps(json_dict[rpc_constants.JSON_RPC_PARAMS]["result"]).decode("utf-8")
        json_dict[rpc_constants.JSON_RPC_PARAMS]["result"] = result
        return orjson.dumps(json_dict), result

    def to_json_bytes_with_cached_result(self, case: Case, cached_result: str) -> bytes:
        # noinspection PyTypeChecker
        params = self.params
        assert isinstance(params, dict)
        params["result"] = cached_result
        return self.to_json_bytes(case)

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
