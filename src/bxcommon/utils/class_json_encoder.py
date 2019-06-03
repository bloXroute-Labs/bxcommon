import json
import traceback
import typing
from datetime import date, time, datetime
from enum import Enum
from inspect import istraceback

SPECIAL_ITERABLE_TYPES = (type(dict().values()), type(dict().keys()),)


def is_iterable_no_collection(o):
    return isinstance(o, SPECIAL_ITERABLE_TYPES) or \
           (isinstance(o, typing.Iterable) and not isinstance(o, typing.Collection))


class ClassJsonEncoder(json.JSONEncoder):

    def default(self, o: typing.Any) -> typing.Any:
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
            return o.isoformat()  # pyre-ignore
        if isinstance(o, bytes):
            try:
                return o.decode("utf-8")
            except UnicodeDecodeError:
                return str(o)
        if hasattr(o, "hexdigest"):
            return o.hexdigest()  # pyre-ignore
        if hasattr(o, "hex_string"):
            return o.hex_string()  # pyre-ignore
        if istraceback(o):
            return "".join(traceback.format_tb(o)).strip()
        return o

    def _encode(self, obj):
        obj = self.default(obj)
        if isinstance(obj, dict):
            return {self.default(self._encode(k)): self._encode(v) for k, v in obj.items()}
        elif isinstance(obj, list) or isinstance(obj, set):
            return [self._encode(l) for l in obj]
        else:
            return obj

    def encode(self, o) -> str:
        return super(ClassJsonEncoder, self).encode(self._encode(o))
