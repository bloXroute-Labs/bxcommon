import importlib
from typing import Any, Optional, Union

from pympler import asizeof


class Sizer:

    def __init__(self, excluded_obj: Optional[Union[object, str]] = None) -> None:
        self.sizer = asizeof.Asizer()
        self.excluded = []

        if excluded_obj is not None:
            self.set_excluded_asizer(excluded_obj)

    def set_excluded_asizer(self, excluded_obj: object) -> Any:
        """
        :param excluded_obj: The string name or an instance of the class you want to exclude from memory calculation

        Sets the attributes of the singleton
        """
        if isinstance(excluded_obj, str):
            module_name, class_name = excluded_obj.rsplit(".", 1)
            class_instance = _str_to_class(module_name, class_name)
        else:
            class_instance = excluded_obj
        if class_instance:
            self.sizer.exclude_types(class_instance)
            self.excluded.append(str(excluded_obj))

    def __repr__(self) -> str:
        return "Sizer(sizer={0.sizer!r}, excluded={0.excluded!r})".format(self)

    def __str__(self) -> str:
        return "Sizer(sizer={0.sizer!s}, excluded={0.excluded!s})".format(self)


def _str_to_class(module_name, class_name):
    """
    Return a class instance from a string reference
    """
    class_instance = None
    try:
        module_instance = importlib.import_module(module_name)
        try:
            class_instance = getattr(module_instance, class_name)
        except AttributeError:
            pass
    except ImportError:
        pass
    return class_instance
