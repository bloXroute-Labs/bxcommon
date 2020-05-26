from enum import Enum
from typing import Optional, Any, Dict

from bxcommon.utils import json_utils


class RpcErrorCode(Enum):
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603

    # implementation specific codes
    # SERVER_ERROR_START = -32000
    ALREADY_SEEN = -32000
    REJECTED = -32001
    # SERVER_ERROR_END = -32099


ERROR_MESSAGE_MAPPINGS = {
    RpcErrorCode.PARSE_ERROR: "Parse error",
    RpcErrorCode.INVALID_REQUEST: "Invalid Request",
    RpcErrorCode.METHOD_NOT_FOUND: "Method not found",
    RpcErrorCode.INVALID_PARAMS: "Invalid params",
    RpcErrorCode.INTERNAL_ERROR: "Internal error",
    RpcErrorCode.ALREADY_SEEN: "Already seen",
    RpcErrorCode.REJECTED: "Rejected",
}


class RpcError(Exception):
    def __init__(self, code: RpcErrorCode, request_id: Optional[str], data: Optional[Any]):
        super().__init__()
        self.code = code
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
        return json_utils.serialize(self.to_json())


class RpcParseError(RpcError):
    def __init__(self, request_id: Optional[str] = None, data: Optional[Any] = None):
        super().__init__(RpcErrorCode.PARSE_ERROR, request_id, data)


class RpcInvalidRequest(RpcError):
    def __init__(self, request_id: Optional[str], data: Optional[Any] = None):
        super().__init__(RpcErrorCode.INVALID_REQUEST, request_id, data)


class RpcMethodNotFound(RpcError):
    def __init__(self, request_id: Optional[str], data: Optional[Any] = None):
        super().__init__(RpcErrorCode.METHOD_NOT_FOUND, request_id, data)


class RpcInvalidParams(RpcError):
    def __init__(self, request_id: Optional[str], data: Optional[Any] = None):
        super().__init__(RpcErrorCode.INVALID_PARAMS, request_id, data)


class RpcInternalError(RpcError):
    def __init__(self, request_id: Optional[str], data: Optional[Any] = None):
        super().__init__(RpcErrorCode.INTERNAL_ERROR, request_id, data)


class RpcAlreadySeen(RpcError):
    def __init__(self, request_id: Optional[str], data: Optional[Any] = None):
        super().__init__(RpcErrorCode.ALREADY_SEEN, request_id, data)


class RpcRejected(RpcError):
    def __init__(self, request_id: Optional[str], data: Optional[Any] = None):
        super().__init__(RpcErrorCode.REJECTED, request_id, data)
