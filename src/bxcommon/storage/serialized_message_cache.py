from typing import NamedTuple

from bxcommon import constants
from bxcommon.rpc.bx_json_rpc_request import BxJsonRpcRequest
from bxcommon.utils.alarm_queue import AlarmQueue
from bxcommon.utils.expiring_dict import ExpiringDict
from bxutils.encoding.json_encoder import Case


class SerializedMessageKey(NamedTuple):
    case: Case
    object_id: int


class SerializedMessageCache:
    _cache: ExpiringDict[SerializedMessageKey, str]

    def __init__(self, alarm_queue: AlarmQueue) -> None:
        self._cache = ExpiringDict(
            alarm_queue,
            constants.SERIALIZED_MESSAGE_CACHE_EXPIRE_TIME_S,
            "serialized_message_cache"
        )

    def serialize_from_cache(self, message: BxJsonRpcRequest, case: Case) -> bytes:
        if constants.USE_SERIALIZED_MESSAGE_CACHE:
            # this functionality is locked behind a feature flag until changes get
            # submitted to orjson for partial serialization functionality
            # otherwise, cached result gets double-serialized as a string, which
            # is undesirable
            params = message.params
            assert isinstance(params, dict)
            key = SerializedMessageKey(case, id(params["result"]))
            if key in self._cache:
                cached_result = self._cache[key]
                result = message.to_json_bytes_with_cached_result(case, cached_result)
                return result
            else:
                message_bytes, cached_result = message.to_json_bytes_split_serialization(case)
                self._cache.add(key, cached_result)
                return message_bytes
        else:
            return message.to_json_bytes(case)
