from collections import deque
from typing import TypeVar, Generic, Deque, Set

T = TypeVar("T")


class LimitedSizeSet(Generic[T]):
    """
    Set with expiration time.
    """

    contents: Set[T]
    _item_tracker: Deque[T]
    _max_size: int

    def __init__(self, max_size: int) -> None:
        self.contents = set()
        self._item_tracker = deque()
        self._max_size = max_size

    def __contains__(self, item: T) -> bool:
        return item in self.contents

    def __iter__(self):
        for item in self.contents:
            yield item

    def remove(self, value: T) -> None:
        """
        Deletion is fairly expensive. Generally, there is no need to delete
        from this data structure.
        """
        self.contents.remove(value)
        self._item_tracker.remove(value)

    def __len__(self) -> int:
        return len(self.contents)

    def add(self, value: T) -> None:
        self.contents.add(value)
        if len(self.contents) != len(self._item_tracker):
            self._make_room_for_new_item()
            self._item_tracker.append(value)

    def _make_room_for_new_item(self) -> None:
        while len(self.contents) > self._max_size:
            key = self._item_tracker.popleft()
            self.contents.remove(key)
