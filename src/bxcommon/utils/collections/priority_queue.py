from typing import Generic, TypeVar, Callable, Any, Dict, Iterator

T = TypeVar("T")


class ObjectPriority(Generic[T]):
    """
    an object wrapper that provide a priority value to it
    the priority value must be a sortable type.
    I.E: implement both __eq__ and __lt__
    """

    def __init__(self, get_priority: Callable[[T], Any], obj: T) -> None:
        self._get_priority = get_priority
        self._obj = obj

    def __repr__(self):
        return f"{self.__class__.__name__}<{self._obj}>"

    def get_priority(self) -> Any:
        return self._get_priority(self._obj)

    def get_object(self) -> T:
        return self._obj


class PriorityQueue(Generic[T]):
    """
     a collection class that sort its items according to their priority.
     items needs to be wrapped with a priority object (ObjectPriority) first, using the add method.
     items needs to be removed from the queue regardless weather they where popped from the queue or not
     in order to remove the priority wrapper they where added with (aka "object tracker").
     sorting by priority should be performed by explicitly call the update_priority method.
     """

    def __init__(self, is_reversed: bool = True) -> None:
        """
        initialize the priority queue collection object.
        :param is_reversed: indicate if the sorting should be performed in revered order.
        """
        self._items_dict: Dict[T, ObjectPriority] = {}
        self._items_tracker: Dict[T, ObjectPriority] = {}
        self._is_reversed = is_reversed

    def __repr__(self):
        return f"{self.__class__.__name__}<{list(self._items_dict.values())}>"

    def __len__(self) -> int:
        return len(self._items_dict)

    def __bool__(self) -> bool:
        return len(self) > 0

    def __iter__(self) -> Iterator[T]:
        for obj in self._items_dict:
            yield obj

    def add(self, item: ObjectPriority[T]) -> None:
        """
        adds a priority item to the queue.
        will track the underlying object until remove is called.
        :param item: see [ObjectPriority] docs
        :raise ValueError: if the item was already added (should call push instead)
        """
        if item.get_object() not in self._items_tracker:
            self._items_tracker[item.get_object()] = item
            self._items_dict[item.get_object()] = item
        else:
            raise ValueError(f"priority item {item} was already added")

    def push(self, obj: T) -> None:
        """
        push an object back to the priority queue
        :param obj: the object to be pushed
        :raise ValueError: if the object was never added to the queue
        """
        if obj in self._items_tracker:
            priority_item = self._items_tracker[obj]
            if obj not in self._items_dict:
                self._items_dict[obj] = priority_item
        else:
            raise self._missing_object_error(obj)

    def remove(self, obj: T) -> None:
        """
        remove an object from the queue
        :param obj: the object to be removed
        """
        try:
            del self._items_tracker[obj]
            del self._items_dict[obj]
        except KeyError:
            pass

    def pop(self) -> T:
        """
        pop an item from the queue, but keep track of its priority wrapper.
        the object will not be included in the priority queue but still needs to be removed from the tracker
        :return: the first item in the priority queue
        """
        obj, _ = self._items_dict.popitem()
        return obj

    def try_remove_from_queue(self, obj: T) -> None:
        """
        attempts to remove an item from the priority queue (not from the tracker).
        :param obj: the object to be removed.
        :raise ValueError: if the object was never added to the queue
        """
        if obj in self._items_tracker:
            try:
                del self._items_dict[obj]
            except KeyError:
                pass
        else:
            raise self._missing_object_error(obj)

    def update_priority(self) -> None:
        """
        updating the priority queue by fetching each object's priority and sort by it.
        sorting is being done according to the is_reversed flag passed in the constructor.
        In case of True, for example: [5, 33, 1, 0, 2, 4] -> [33, 5, 4, 2, 1, 0]
        this method has at least O(n log n) complexity and should be called as less frequent as possible.
        """
        sorted_items = sorted(self._items_dict.values(), key=lambda p: p.get_priority(), reverse=self._is_reversed)
        new_items_dict = {}
        for item in sorted_items:
            new_items_dict[item.get_object()] = item

        self._items_dict = new_items_dict

    def _missing_object_error(self, obj) -> ValueError:
        return ValueError(f"object {obj} is missing in items tracker {self._items_tracker}")
