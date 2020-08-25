import json
import os
import traceback
from datetime import date, time, datetime
from enum import Enum
from inspect import istraceback
from typing import Union, Any, Iterable, Collection, Optional, Dict

from bxutils import logging

logger = logging.get_logger(__name__)

SPECIAL_ITERABLE_TYPES = (type(dict().values()), type(dict().keys()),)


class Case(Enum):
    SNAKE = 1
    CAMEL = 2


def is_iterable_no_collection(o):
    return isinstance(o, SPECIAL_ITERABLE_TYPES) or \
           (isinstance(o, Iterable) and not isinstance(o, Collection))


def to_json(obj: Any, remove_nulls: bool = False) -> str:
    if remove_nulls:
        clean_dict = {}
        for key, value in obj.__dict__.items():
            if value:
                clean_dict[key] = value
        return json.dumps(clean_dict, cls=EnhancedJSONEncoder)

    return json.dumps(obj, cls=EnhancedJSONEncoder)


def to_dict(obj: Any) -> Dict[str, Any]:
    return EnhancedJSONEncoder().as_dict(obj)


def load_json_from_file(json_file_path: str) -> Optional[Union[list, dict]]:
    node_json = None

    if os.path.isfile(json_file_path):
        try:
            with open(json_file_path) as json_file:
                node_json = json.load(json_file)
        except ValueError as e:
            logger.debug("Failed to parse json: %s", e)
        except OSError as e:
            logger.debug("Failed trying to check for a json file: %s", e)
    else:
        raise ValueError("Could not locate json file: %s", json_file_path)

    return node_json


class EnhancedJSONEncoder(json.JSONEncoder):
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
        elif isinstance(obj, list) or isinstance(obj, set):
            return [self._encode(l) for l in obj]
        else:
            return obj

    def encode(self, o) -> str:
        return super(EnhancedJSONEncoder, self).encode(self._encode(o))

    def as_dict(self, obj) -> Dict[str, Any]:
        return self._encode(obj)
