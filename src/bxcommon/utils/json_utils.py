import json
from typing import Any

from bxcommon.utils.class_json_encoder import ClassJsonEncoder


def serialize(obj: Any) -> str:
    """
    Serializes object into a string JSON

    :param obj: object to serialize
    :return: JSON string
    """
    return json.dumps(obj, cls=ClassJsonEncoder)
