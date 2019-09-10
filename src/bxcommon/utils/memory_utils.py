import resource
import sys
from abc import ABC, abstractmethod
from pympler import asizeof
from pympler.asizeof import Asized
from sys import getsizeof
from bxcommon import constants
from typing import Union, Deque, Set, Any, List, Optional, NamedTuple
DEFAULT_DETAILED_MEMORY_BREAKDOWN_LIMIT = 50 * 1024


class SpecialTuple(NamedTuple):
    size: int
    seen_ids: Set[int]


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


class SpecialMemoryProperties(ABC):
    """
    Meta class that should be implemented in all classes with special memory types
    """

    @abstractmethod
    def special_memory_size(self, ids: Optional[Set[int]] = None) -> SpecialTuple:
        if ids is None:
            ids = set()
        return SpecialTuple(size=0, seen_ids=ids)


def get_app_memory_usage():
    # type: () -> int
    """
    Provides total application memory usage in bytes
    :return: int
    """
    mem_usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

    # resource.getrusage provides memory usage in bytes on OSX but in kilo bytes for other platforms
    if sys.platform != constants.PLATFORM_MAC:
        mem_usage *= 1024

    return mem_usage


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


def _get_special_size_helper(obj: Union[Deque, Set[Any], memoryview, List], ids: Set[int]) -> SpecialTuple:
    """
    Calculates total size memory consumed by special objects and all special objects that it references
    :param obj: object to calculate size
    :param ids: set of already seen ids
    :return: Tuple of the size in bytes of the special data structures of that object, and the integer keys associated
    with those objects and their special contents
    """
    default_size = getsizeof(0)
    total_size = 0
    if id(obj) not in ids:
        if isinstance(obj, memoryview):
            total_size += getsizeof(obj, default_size)
            if id(obj.obj) not in ids:  # pyre-ignore
                total_size += obj.nbytes  # pyre-ignore
                ids.add(id(obj.obj))  # pyre-ignore
            ids.add(id(obj))
            return SpecialTuple(size=total_size, seen_ids=ids)
        # The size of deques and memoryviews are not properly recorded using get_object_size
        elif isinstance(obj, Deque):
            total_size += getsizeof(obj, default_size)
            for elem in obj:
                if isinstance(elem, (Deque, Set, memoryview, List)):
                    curr_size, ids = _get_special_size_helper(elem, ids)
                    total_size += curr_size
                else:
                    total_size += get_object_size(elem).size
                ids.add(id(elem))
        else:
            for elem in obj:
                if isinstance(elem, (Deque, Set, memoryview, List)):
                    curr_size, ids = _get_special_size_helper(elem, ids)
                    total_size += curr_size
                    ids.add(id(elem))
        ids.add(id(obj))
    return SpecialTuple(size=total_size, seen_ids=ids)


def get_special_size(obj: Any, ids: Optional[Set[int]] = None) -> SpecialTuple:
    """
    Handles size requests for classes and data structures
    :param obj: object to calculate size
    :param ids: set of already seen ids
    :return: Tuple of the size in bytes of the special data structures of that object, and the integer keys associated
    with those objects and their special contents
    """
    if ids is None:
        ids = set()
    if obj is None:
        ids.add(obj)
        return SpecialTuple(size=0, seen_ids=ids)
    if isinstance(obj, SpecialMemoryProperties):
        return obj.special_memory_size(ids)
    elif isinstance(obj, (Deque, Set, memoryview, List)):
        return _get_special_size_helper(obj, ids)
    else:
        return SpecialTuple(size=0, seen_ids=ids)


def add_special_objects(*args, ids: Optional[Set[int]] = None) -> SpecialTuple:
    """
    Should be called by class methods with arguments consisting of attributes of the class that are objects
    with deques, memoryviews, etc. within them ...
    OR
    deques, memoryviews, etc. data structures themselves
    See AbstractConnection, InputBuffer, for examples
    :param args: attributes of a class to be used in the special size calculation
    :param ids: set of already seen ids
    :return: Tuple of the size in bytes of the special data structures of that object, and the integer keys associated
    with those objects and their special contents
    """
    total_size = 0
    if ids is None:
        ids = set()
    for obj in args:
        curr_size, ids = get_special_size(obj, ids=ids)
        total_size += curr_size
    return SpecialTuple(size=total_size, seen_ids=ids)
