import resource

from pympler import asizeof
from pympler.asizeof import Asized

# Default to 50 kB
DEFAULT_DETAILED_MEMORY_BREAKDOWN_LIMIT = 50 * 1024


class ObjectSize(object):
    """
    Represents size of object with detailed breakdown by object field
    """

    def __init__(self, name=None, size=0, flat_size=0, references=None, is_actual_size=True):
        self.name = name
        self.size = size
        self.flat_size = flat_size
        self.references = references
        self.is_actual_size = is_actual_size


def get_app_memory_usage():
    # type: () -> int
    """
    Provides total application memory usage in bytes
    :return: int
    """
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss


def get_object_size(obj):
    # type: (object) -> ObjectSize
    """
    Calculates total size memory consumed by objects and all objects that it references
    :param obj: object to calculate size
    :return: object representing memory usage breakdown for the object
    """
    obj_size = asizeof.asized(obj)
    return _to_size_obj(obj_size, DEFAULT_DETAILED_MEMORY_BREAKDOWN_LIMIT)


def get_detailed_object_size(obj, detailed_if_greater_than=DEFAULT_DETAILED_MEMORY_BREAKDOWN_LIMIT):
    # type: (object, int) -> ObjectSize
    """
    Calculates total size memory consumed by objects and all objects that it references.
    Generates breakdown by reference.
    :param obj: object to calculate size
    :param detailed_if_greater_than: break down memory by fields of object if it is size is greater than provided value
    :return: object representing memory usage breakdown for the object
    """
    obj_size = asizeof.asized(obj, detail=10)
    return _to_size_obj(obj_size, detailed_if_greater_than)


def _to_size_obj(obj_size, detailed_if_greater_than):
    # type: (Asized, int) -> ObjectSize
    references = []

    if obj_size.refs is not None:
        for ref in obj_size.refs:
            size_obj = _to_size_obj(ref, detailed_if_greater_than)
            if size_obj.size > detailed_if_greater_than:
                references.append(size_obj)

    return ObjectSize(obj_size.name, obj_size.size, obj_size.flat, references)
