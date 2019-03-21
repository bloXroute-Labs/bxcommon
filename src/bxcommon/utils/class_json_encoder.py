import json
import typing
from datetime import datetime


def is_iterable_no_collection(o):
    return isinstance(o, typing.Iterable) and not isinstance(o, typing.Collection)


class ClassJsonEncoder(json.JSONEncoder):

    def default(self, o):
        if is_iterable_no_collection(o):
            o = list(o)
        elif isinstance(o, (bytearray, memoryview)):
            o = bytes(o)
        if hasattr(o, '__dict__'):
            if isinstance(o.__dict__, dict):
                return o.__dict__
            else:
                return str(o)
        if isinstance(o, datetime):
            return o.__str__()
        if isinstance(o, bytes):
            try:
                return o.decode("utf-8")
            except UnicodeDecodeError:
                return str(o)

        return o

    def _encode(self, obj):
        if hasattr(obj, "__dict__") and isinstance(obj.__dict__, dict):
            obj = obj.__dict__
        if isinstance(obj, dict):
            return {self.default(self._encode(k)): self._encode(v) for k, v in obj.items()}
        elif isinstance(obj, list) or isinstance(obj, set):
            return [self._encode(l) for l in obj]
        else:
            return obj

    def encode(self, obj):
        return super(ClassJsonEncoder, self).encode(self._encode(obj))
