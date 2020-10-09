# pyre-ignore-all-errors
# This file does type manipulation that type checkers will not understand.

import dataclasses
import json
from enum import Flag
from typing import Dict, Type, TypeVar, Any, List, Optional, Union, Set

import humps

from bxcommon.utils import convert
from bxutils import log_messages
from bxutils import logging
from bxutils.encoding.json_encoder import Case

logger = logging.get_logger(__name__)
T = TypeVar("T")
_TYPE_HANDLER_MAPPING = {}
STRING_PARSING_METHOD = "from_string"
DICT_PARSING_METHOD = "from_json"


def load_model_from_json(
    model_class: Type[T], model_params: str, model_case: Case = Case.SNAKE
) -> T:
    try:
        model_dict = json.loads(model_params)
        return load_model(model_class, model_dict, model_case)
    except Exception:
        logger.error(log_messages.ERROR_LOADING_MODEL_INTO_DICT, model_class, model_params)
        raise


def load_model(
    model_class: Type[T],
    model_params: Dict[str, Any],
    model_case: Case = Case.SNAKE
) -> T:
    """
    Loads a model class instance from the dictionary.

    This function ensures that models are forward compatible. If attributes are
    added to models in future versions, and those versions are serialized somewhere
    (e.g. Redis), this function ensures that only attributes that the current
    version knows about are loaded.

    :param model_class: class of the model to load into
    :param model_params: attributes from the retrieved model to load
    :param model_case: case of the attribute names from the retrieved model
                       these attribute names will be converted to snake_case for lookup
                       of type information
    :return: instance of model class
    """
    try:
        attributes = {}
        for attribute in dataclasses.fields(model_class):
            if model_case == Case.SNAKE:
                model_attribute_name = attribute.name
            else:
                model_attribute_name = humps.camelize(attribute.name)
            if model_attribute_name in model_params:
                attributes[attribute.name] = _load_attribute(
                    attribute.type,
                    model_params[model_attribute_name],
                    model_case=model_case
                )
        return model_class(**attributes)
    except Exception as e:
        raise TypeError(
            f"Could not load model of type {model_class} from data: {model_params}"
        ) from e


# pylint: disable=too-many-return-statements,too-many-branches
def _load_attribute(
    attribute_type: Type[T],
    attribute_value: Any,
    cast_basic_values: bool = True,
    model_case: Case = Case.SNAKE,
) -> Optional[T]:
    """
    Loads an attribute and attempts to cast it to the correct class type.

    For any type with a custom `from_string` method, attempt to construct using that method.
    For data classes, recurse and attempt to load the original model.
    For Any types, None values, or Generic types, return the provided value as is.
    For built in `typing` types, special handling is generally required. List/Dict/... have been implemented for now.
    For Flag enum types, use the Flag name for loading / writing.
    For basic types, construct the objects normally.
    :param attribute_type: class of the attribute to load
    :param attribute_value: attribute value to parse
    :param cast_basic_values: if to cast between str, int, etc.
    :return: instance of attribute value
    """
    if (
        isinstance(attribute_value, str)
        and hasattr(attribute_type, STRING_PARSING_METHOD)
        and callable(getattr(attribute_type, STRING_PARSING_METHOD))
    ):
        return getattr(attribute_type, STRING_PARSING_METHOD)(attribute_value)
    elif (
        isinstance(attribute_value, dict)
        and hasattr(attribute_type, DICT_PARSING_METHOD)
        and callable(getattr(attribute_type, DICT_PARSING_METHOD))
    ):
        return getattr(attribute_type, DICT_PARSING_METHOD)(attribute_value)
    elif hasattr(attribute_type, "__annotations__"):
        return load_model(attribute_type, attribute_value, model_case)
    elif attribute_type == Any or attribute_value is None or attribute_type.__class__ == TypeVar:
        return attribute_value
    elif hasattr(attribute_type, "__origin__"):
        if attribute_type.__origin__ in _TYPE_HANDLER_MAPPING:
            return _TYPE_HANDLER_MAPPING[attribute_type.__origin__](
                attribute_type, attribute_value, model_case
            )
        else:
            raise NotImplementedError(
                f"Model loader is not capable of loading a "
                f"{attribute_type.__origin__} type. Please implement a handler."
            )
    elif issubclass(attribute_type, Flag):
        return attribute_type[str(attribute_value)]
    else:
        if cast_basic_values:
            try:
                return attribute_type(attribute_value)
            except Exception as e:
                # backup processing for hex string types
                try:
                    if attribute_type == int:
                        return int(attribute_value, 16)
                    if attribute_type == bytearray:
                        return convert.hex_to_bytes(attribute_value)
                except Exception as _e:
                    raise e
                raise e
        elif not isinstance(attribute_value, attribute_type):
            raise TypeError(f"{attribute_value} is not of type {attribute_type}.")
        else:
            return attribute_value


def _load_list(list_type: Type[T], list_value: Any, model_case: Case) -> List:
    if isinstance(list_value, dict):
        raise ValueError("Forcibly raising when trying to cast Dict to List.")

    if len(list_type.__args__) != 1:
        raise ValueError("List type annotation requires 1 or 0 args.")

    list_param = list_type.__args__[0]
    return [
        _load_attribute(list_param, list_entry, model_case=model_case)
        for list_entry in list_value
    ]


def _load_set(set_type: Type[T], set_value: Any, model_case: Case) -> Set:
    if isinstance(set_value, dict):
        raise ValueError("Forcibly raising when trying to cast Dict to Set.")

    if len(set_type.__args__) != 1:
        raise ValueError("List type annotation requires 1 or 0 args.")

    set_param = set_type.__args__[0]
    return {
        _load_attribute(set_param, set_entry, model_case=model_case)
        for set_entry in set_value
    }


def _load_dict(dict_type: Type[T], dict_value: Any, model_case: Case) -> Dict:
    if not isinstance(dict_value, Dict):
        raise TypeError("Cannot deserialize value {} to Dict type {}".format(dict_value, dict_type))

    if len(dict_type.__args__) != 2:
        raise ValueError("Dict type annotation requires 2 or 0 args.")

    key_type = dict_type.__args__[0]
    value_type = dict_type.__args__[1]
    return {
        _load_attribute(
            key_type, key, model_case=model_case
        ): _load_attribute(value_type, value, model_case=model_case)
        for key, value in dict_value.items()
    }


def _load_optional(optional_type: Type[T], optional_value: Any, model_case: Case) -> Optional:
    if len(optional_type.__args__) != 1:
        raise ValueError("Optional types must have a type annotation.")

    optional_param = optional_type.__args__[0]
    return _load_attribute(optional_param, optional_value, model_case=model_case)


def _load_union(union_type: Type[T], union_value: Any, model_case: Case) -> Any:
    # pylint: disable=unidiomatic-typecheck
    if len(union_type.__args__) == 2 and type(None) in union_type.__args__:
        # special case of an optional
        return _load_attribute(union_type.__args__[0], union_value, model_case=model_case)
    else:
        for union_param in union_type.__args__:
            # noinspection PyBroadException
            try:
                return _load_attribute(
                    union_param, union_value, cast_basic_values=False, model_case=model_case
                )
            # pylint: disable=broad-except
            except Exception as _e:
                continue
        raise NotImplementedError(
            f"Could not find a union type that matched value. "
            f"Types: {union_type.__args__}, Value: {union_value}"
        )


_TYPE_HANDLER_MAPPING.update({
    list: _load_list,
    List: _load_list,
    set: _load_set,
    Set: _load_set,
    dict: _load_dict,
    Dict: _load_dict,
    Optional: _load_optional,
    Union: _load_union,
})
