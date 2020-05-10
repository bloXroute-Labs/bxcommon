import json
import traceback
from datetime import date, time, datetime
from enum import Enum
from inspect import istraceback
from typing import Collection, Any, Iterable

SPECIAL_ITERABLE_TYPES = (type(dict().values()), type(dict().keys()),)

"""
this module is deprecated, and will be removed in the next iteration.
please use bxutils.encoding.json_encoder instead
"""


# pylint: disable=invalid-name
def is_iterable_no_collection(o):
    return isinstance(o, SPECIAL_ITERABLE_TYPES) or \
           (isinstance(o, Iterable) and not isinstance(o, Collection))


# pylint: disable=invalid-name,too-many-return-statements,method-hidden
class ClassJsonEncoder(json.JSONEncoder):

    def default(self, o: Any) -> Any:
        if is_iterable_no_collection(o):
            o = list(o)
        elif isinstance(o, (bytearray, memoryview)):
            o = bytes(o)
        if isinstance(o, Enum):
            return str(o)
        if hasattr(o, "__dict__"):
            if isinstance(o.__dict__, dict):
                return o.__dict__
            else:
                return str(o)
        if isinstance(o, (date, datetime, time)):
            return o.isoformat()
        if isinstance(o, bytes):
            try:
                return o.decode("utf-8")
            except UnicodeDecodeError:
                return str(o)
        if hasattr(o, "hexdigest"):
            return o.hexdigest()
        if hasattr(o, "hex_string"):
            return o.hex_string()
        if istraceback(o):
            return "".join(traceback.format_tb(o)).strip()
        return o

    def _encode(self, obj):
        obj = self.default(obj)
        if isinstance(obj, dict):
            return {self.default(self._encode(k)): self._encode(v) for k, v in obj.items()}
        elif isinstance(obj, (list, set)):
            return [self._encode(l) for l in obj]
        else:
            return obj

    def encode(self, o) -> str:
        return super(ClassJsonEncoder, self).encode(self._encode(o))
