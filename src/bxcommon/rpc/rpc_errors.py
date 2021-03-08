import json
from enum import Enum
from typing import Optional, Any, Dict

from bxutils.encoding import json_encoder


class RpcErrorCode(Enum):
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603

    # implementation specific codes
    SERVER_ERROR = -32000
    BLOCKED = -32001
    TIMED_OUT = -32002
    ACCOUNT_ID_ERROR = -32003
    UNKNOWN = -32004
    WS_CONNECTIONS_EXCEEDED = -32005


ERROR_MESSAGE_MAPPINGS = {
    RpcErrorCode.PARSE_ERROR: "Parse error",
    RpcErrorCode.INVALID_REQUEST: "Invalid request",
    RpcErrorCode.METHOD_NOT_FOUND: "Invalid method",
    RpcErrorCode.INVALID_PARAMS: "Invalid params",
    RpcErrorCode.INTERNAL_ERROR: "Internal error",
    RpcErrorCode.BLOCKED: "Insufficient quota",
    RpcErrorCode.TIMED_OUT: "Timeout error",
    RpcErrorCode.ACCOUNT_ID_ERROR: "Invalid Account ID",
    RpcErrorCode.UNKNOWN: "Invalid result from BDN",
    RpcErrorCode.WS_CONNECTIONS_EXCEEDED: "Ws connections exceeded",
}


class RpcError(Exception):
    def __init__(
        self,
        code: RpcErrorCode,
        request_id: Optional[str],
        data: Optional[Any],
        message: Optional[str] = None,
    ) -> None:
        super().__init__()
        self.code = code
        if message:
            self.message = message
        else:
            self.message = ERROR_MESSAGE_MAPPINGS[code]
        self.data = data
        self.id = request_id

    def to_json(self) -> Dict[str, Any]:
        fields = {
            "code": self.code.value,
            "message": self.message,
        }
        if self.data is not None:
            fields["data"] = self.data
        return fields

    def to_jsons(self) -> str:
        return json_encoder.to_json(self.to_json())

    @classmethod
    def from_json(cls, payload: Dict[str, Any]) -> "RpcError":
        return cls(
            RpcErrorCode(payload["code"]),
            None,
            payload.get("data"),
            payload.get("message"),
        )

    @classmethod
    def from_jsons(cls, payload: str) -> "RpcError":
        return cls.from_json(json.loads(payload))


class RpcParseError(RpcError):
    def __init__(
        self, request_id: Optional[str] = None, data: Optional[Any] = None
    ) -> None:
        super().__init__(RpcErrorCode.PARSE_ERROR, request_id, data)


class RpcInvalidRequest(RpcError):
    def __init__(self, request_id: Optional[str], data: Optional[Any] = None) -> None:
        super().__init__(RpcErrorCode.INVALID_REQUEST, request_id, data)


class RpcMethodNotFound(RpcError):
    def __init__(self, request_id: Optional[str], data: Optional[Any] = None) -> None:
        super().__init__(RpcErrorCode.METHOD_NOT_FOUND, request_id, data)


class RpcInvalidParams(RpcError):
    def __init__(self, request_id: Optional[str], data: Optional[Any] = None) -> None:
        super().__init__(RpcErrorCode.INVALID_PARAMS, request_id, data)


class RpcInternalError(RpcError):
    def __init__(self, request_id: Optional[str], data: Optional[Any] = None) -> None:
        super().__init__(RpcErrorCode.INTERNAL_ERROR, request_id, data)


class RpcBlocked(RpcError):
    def __init__(self, request_id: Optional[str], data: Optional[Any] = None) -> None:
        super().__init__(RpcErrorCode.BLOCKED, request_id, data)


class RpcTimedOut(RpcError):
    def __init__(self, request_id: Optional[str], data: Optional[Any] = None) -> None:
        super().__init__(RpcErrorCode.TIMED_OUT, request_id, data)


class RpcAccountIdError(RpcError):
    def __init__(self, request_id: Optional[str], data: Optional[Any] = None) -> None:
        super().__init__(RpcErrorCode.ACCOUNT_ID_ERROR, request_id, data)


class RpcUnknownError(RpcError):
    def __init__(self, request_id: Optional[str], data: Optional[Any] = None) -> None:
        super().__init__(RpcErrorCode.UNKNOWN, request_id, data)


class RpcWsConnectionExceededError(RpcError):
    def __init__(
        self, request_id: Optional[str] = None, data: Optional[Any] = None
    ) -> None:
        super().__init__(RpcErrorCode.WS_CONNECTIONS_EXCEEDED, request_id, data)
