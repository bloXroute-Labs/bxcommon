from collections import deque
from typing import TypeVar, Generic, Dict, Deque, Optional

KT = TypeVar("KT")
VT = TypeVar("VT")


class LimitedSizeDict(Generic[KT, VT]):
    """
    Dictionary with expiration time.
    """

    contents: Dict[KT, VT]
    key_tracker: Deque[KT]
    _max_size: int

    def __init__(self, max_size: int) -> None:
        self.contents = {}
        self.key_tracker = deque()
        self._max_size = max_size

    def __contains__(self, item: KT) -> bool:
        return item in self.contents

    def __setitem__(self, key: KT, value: VT) -> None:
        if key in self.contents:
            self.contents[key] = value
        else:
            self.add(key, value)

    def __delitem__(self, key: KT) -> None:
        """
        Deletion is fairly expensive. Generally, there is no need to delete
        from this data structure.
        """
        del self.contents[key]
        self.key_tracker.remove(key)

    def __getitem__(self, item: KT) -> VT:
        return self.contents[item]

    def __len__(self) -> int:
        return len(self.contents)

    def add(self, key: KT, value: VT) -> None:
        self._make_room_for_new_item()

        self.contents[key] = value
        self.key_tracker.append(key)

    def get(self, key: KT, default: Optional[VT] = None) -> Optional[VT]:
        return self.contents.get(key, default)

    def _make_room_for_new_item(self) -> None:
        while len(self.key_tracker) >= self._max_size:
            key = self.key_tracker.popleft()
            del self.contents[key]
