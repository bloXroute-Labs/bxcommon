import time

from collections import OrderedDict
from typing import TypeVar, Generic, Optional, Callable, Dict, Any

T = TypeVar("T")


class ExpirationQueue(Generic[T]):
    """
    Handles queue of item that need to be expired and removed from the queue over time
    """

    time_to_live_sec: int
    # NOTE: this cannot be annotated as an collections.OrderedDict
    queue: Dict[T, float]

    def __init__(self, time_to_live_sec: int) -> None:

        if time_to_live_sec < 0:
            raise ValueError("Time to live cannot be negative.")

        self.time_to_live_sec = time_to_live_sec
        self.queue = OrderedDict()

    def __len__(self) -> int:
        return len(self.queue)

    def __bool__(self) -> bool:
        return len(self) > 0

    def add(self, item: T) -> None:
        """
        Adds item to the queue
        :param item: item
        """
        self.queue[item] = time.time()

    def remove(self, item: T) -> None:
        """
        Removes item from expiration queue
        :param item: item to remove
        """
        if item in self.queue:
            del self.queue[item]

    def remove_expired(
        self,
        current_time: Optional[float] = None,
        remove_callback: Optional[Callable[[T], Any]] = None,
        limit: Optional[int] = None,
        **kwargs
    ):
        """
        Removes expired items from the queue
        :param current_time: time to use as current time for expiration
        :param remove_callback: reference to a callback function that is being called when item is removed
        :param limit: max number of entries to remove in one call
        :param kwargs: keyword args to pass into the callback method
        """
        if current_time is None:
            current_time = time.time()
        if limit is None:
            limit = len(self.queue)

        iterations = 0
        while (
            len(self.queue) > 0 and
            iterations < limit and
            # pyre-fixme[6]: Expected `float` for 1st param but got `Optional[float]`.
            current_time - self.get_oldest_item_timestamp() > self.time_to_live_sec
        ):
            # noinspection PyArgumentList
            # pyre-fixme[28]: Unexpected keyword argument `last`.
            item, _timestamp = self.queue.popitem(last=False)

            if remove_callback is not None:
                remove_callback(item, **kwargs)

            iterations += 1

    def get_oldest(self) -> Optional[T]:
        """
        Returns the value of oldest item in the queue
        :return: value of oldest item
        """
        if not self.queue:
            return None

        return next(iter(self.queue.keys()))

    def get_oldest_item_timestamp(self) -> Optional[float]:
        """
        Returns timestamp of the oldest item
        :return: timestamp of the oldest item
        """
        if not self.queue:
            return None

        oldest_item = self.get_oldest()
        assert oldest_item is not None
        return self.queue[oldest_item]

    def remove_oldest(
        self, remove_callback: Optional[Callable[[T], None]] = None, **kwargs
    ) -> None:
        """
        Remove one oldest item from the queue
        :param remove_callback: reference to a callback function that is being called when item is removed
        """
        if len(self.queue) > 0:
            # pyre-fixme[28]: Unexpected keyword argument `last`.
            item, _timestamp = self.queue.popitem(last=False)

            if remove_callback is not None:
                remove_callback(item, **kwargs)

    def clear(self) -> None:
        self.queue.clear()
