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


def is_iterable_no_collection(obj):
    return isinstance(obj, SPECIAL_ITERABLE_TYPES) or \
           (isinstance(obj, Iterable) and not isinstance(obj, Collection))


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
            logger.debug("Failed to parse json: {}", e)
        except OSError as e:
            logger.debug("Failed trying to check for a json file: {}", e)
    else:
        raise ValueError(f"Could not locate json file: {json_file_path}")

    return node_json


class EnhancedJSONEncoder(json.JSONEncoder):
    # pylint: disable=method-hidden,too-many-return-statements,arguments-differ
    # pyre-fixme[14]: `default` overrides method defined in `JSONEncoder`
    #  inconsistently.
    def default(self, obj: Any) -> Any:
        if is_iterable_no_collection(obj):
            obj = list(obj)
        elif isinstance(obj, (bytearray, memoryview)):
            obj = bytes(obj)
        if isinstance(obj, Enum):
            return str(obj)
        if hasattr(obj, "__dict__"):
            if isinstance(obj.__dict__, dict):
                return obj.__dict__
            else:
                return str(obj)
        if isinstance(obj, (date, datetime, time)):
            return obj.isoformat()
        if isinstance(obj, bytes):
            try:
                return obj.decode("utf-8")
            except UnicodeDecodeError:
                return str(obj)
        if hasattr(obj, "hexdigest"):
            return obj.hexdigest()
        if hasattr(obj, "hex_string"):
            return obj.hex_string()
        if istraceback(obj):
            return "".join(traceback.format_tb(obj)).strip()
        return obj

    def _encode(self, obj):
        obj = self.default(obj)
        if isinstance(obj, dict):
            return {self.default(self._encode(k)): self._encode(v) for k, v in obj.items()}
        elif isinstance(obj, (list, set)):
            return [self._encode(l) for l in obj]
        else:
            return obj

    def encode(self, o) -> str:
        return super(EnhancedJSONEncoder, self).encode(self._encode(o))

    def as_dict(self, obj) -> Dict[str, Any]:
        return self._encode(obj)
