# pyre-ignore-all-errors
# This file does type manipulation that type checkers will not understand.

import dataclasses
import json
from enum import Flag
from typing import Dict, Type, TypeVar, Any, List, Optional, Union, Set

from bxutils import log_messages
from bxutils import logging

logger = logging.get_logger(__name__)
T = TypeVar("T")
_TYPE_HANDLER_MAPPING = {}


def load_model_from_json(model_class: Type[T], model_params: str) -> T:
    try:
        model_dict = json.loads(model_params)
        return load_model(model_class, model_dict)
    except Exception:
        logger.error(log_messages.ERROR_LOADING_MODEL_INTO_DICT, model_class, model_params)
        raise


def load_model(model_class: Type[T], model_params: Dict[str, Any]) -> T:
    """
    Ensures models are forward compatible - if attributes are added to models in future versions and these models saved
    to Redis, this function ensures that only the attributes that the current version knows about are loaded
    :param model_class: Class of the model to load into
    :param model_params: Attributes from the retrieved model to load
    :return: instance of model class
    """
    try:
        attributes = {}
        for attribute in dataclasses.fields(model_class):
            if attribute.name in model_params:
                attributes[attribute.name] = _load_attribute(attribute.type, model_params[attribute.name])
        return model_class(**attributes)
    except Exception as e:
        raise TypeError("Could not load model of type {} from data: {}".format(model_class, model_params)) from e


def _load_attribute(attribute_type: Type[T], attribute_value: Any, cast_basic_values: bool = True) -> Optional[T]:
    """
    Loads an attribute and attempts to cast it to the correct class type.
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
    if hasattr(attribute_type, "__annotations__"):
        return load_model(attribute_type, attribute_value)
    elif attribute_type == Any or attribute_value is None or attribute_type.__class__ == TypeVar:
        return attribute_value
    elif hasattr(attribute_type, "__origin__"):
        if attribute_type.__origin__ in _TYPE_HANDLER_MAPPING:
            return _TYPE_HANDLER_MAPPING[attribute_type.__origin__](attribute_type, attribute_value)
        else:
            raise NotImplementedError("Model loader is not capable of loading a {} type. Please implement a handler."
                                      .format(attribute_type.__origin__))
    elif issubclass(attribute_type, Flag):
        return attribute_type[str(attribute_value)]
    else:
        if cast_basic_values:
            return attribute_type(attribute_value)
        elif not isinstance(attribute_value, attribute_type):
            raise TypeError("{} is not of type {}.".format(attribute_value, attribute_type))
        else:
            return attribute_value


def _load_list(list_type: Type[T], list_value: Any) -> List:
    if isinstance(list_value, dict):
        raise ValueError("Forcibly raising when trying to cast Dict to List.")

    if len(list_type.__args__) != 1:
        raise ValueError("List type annotation requires 1 or 0 args.")

    list_param = list_type.__args__[0]
    return [_load_attribute(list_param, list_entry) for list_entry in list_value]


def _load_set(set_type: Type[T], set_value: Any) -> Set:
    if isinstance(set_value, dict):
        raise ValueError("Forcibly raising when trying to cast Dict to Set.")

    if len(set_type.__args__) != 1:
        raise ValueError("List type annotation requires 1 or 0 args.")

    set_param = set_type.__args__[0]
    return {_load_attribute(set_param, set_entry) for set_entry in set_value}


def _load_dict(dict_type: Type[T], dict_value: Any) -> Dict:
    if not isinstance(dict_value, Dict):
        raise TypeError("Cannot deserialize value {} to Dict type {}".format(dict_value, dict_type))

    if len(dict_type.__args__) != 2:
        raise ValueError("Dict type annotation requires 2 or 0 args.")

    key_type = dict_type.__args__[0]
    value_type = dict_type.__args__[1]
    return {_load_attribute(key_type, key): _load_attribute(value_type, value) for key, value in dict_value.items()}


def _load_optional(optional_type: Type[T], optional_value: Any) -> Optional:
    if len(optional_type.__args__) != 1:
        raise ValueError("Optional types must have a type annotation.")

    optional_param = optional_type.__args__[0]
    return _load_attribute(optional_param, optional_value)


def _load_union(union_type: Type[T], union_value: Any) -> Any:
    # pylint: disable=unidiomatic-typecheck
    if len(union_type.__args__) == 2 and type(None) in union_type.__args__:
        # special case of an optional
        return _load_attribute(union_type.__args__[0], union_value)
    else:
        for union_param in union_type.__args__:
            # noinspection PyBroadException
            try:
                return _load_attribute(union_param, union_value, cast_basic_values=False)
            # pylint: disable=broad-except
            except Exception as _e:
                continue
        raise NotImplementedError(
            f"Could not find a union type that matched value. "
            f"Types: {union_type.__args__}, Value: {union_value}"
        )


# noinspection PyRedeclaration
_TYPE_HANDLER_MAPPING = {
    list: _load_list,
    List: _load_list,
    set: _load_set,
    Set: _load_set,
    dict: _load_dict,
    Dict: _load_dict,
    Optional: _load_optional,
    Union: _load_union,
}
