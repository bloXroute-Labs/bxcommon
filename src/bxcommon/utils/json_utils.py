import json
from typing import Any

from bxutils.encoding.json_encoder import EnhancedJSONEncoder


def serialize(obj: Any) -> str:
    """
    Serializes object into a string JSON
    DEPRECATED use json_encoder.to_json directly

    :param obj: object to serialize
    :return: JSON string
    """
    return json.dumps(obj, cls=EnhancedJSONEncoder)
