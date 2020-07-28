from typing import List, TypeVar, Generic, Set

from bxcommon.utils.alarm_queue import AlarmQueue
from bxcommon.utils.expiration_queue import ExpirationQueue
from bxutils import logging

T = TypeVar("T")
logger = logging.get_logger(__name__)


class ExpiringSet(Generic[T]):
    """
    Set with expiration time.
    """

    contents: Set[T]
    _alarm_queue: AlarmQueue
    _expiration_queue: ExpirationQueue[T]
    _expiration_time: int
    _log_removal: bool
    _name: str

    def __init__(
        self, alarm_queue: AlarmQueue, expiration_time_s: int, name: str, log_removal: bool = False
    ):
        self.contents = set()
        self._alarm_queue = alarm_queue
        self._expiration_queue = ExpirationQueue(expiration_time_s)
        self._expiration_time = expiration_time_s
        self._log_removal = log_removal
        self._name = name

    def __contains__(self, item: T) -> bool:
        return item in self.contents

    def __len__(self) -> int:
        return len(self.contents)

    def add(self, item: T) -> None:
        self.contents.add(item)
        self._expiration_queue.add(item)
        self._alarm_queue.register_approx_alarm(
            self._expiration_time * 2,
            self._expiration_time,
            self.cleanup,
            alarm_name=f"ExpiringSet[{self._name}]#cleanup"
        )

    def remove(self, item: T) -> None:
        self.contents.remove(item)

    def get_recent_items(self, count: int) -> List[T]:
        items = []
        # noinspection PyTypeChecker
        entries = reversed(self._expiration_queue.queue.keys())

        try:
            for _ in range(count):
                items.append(next(entries))
        except StopIteration as _e:
            logger.debug("Attempted to fetch {} entries, but only {} existed.", count, len(items))

        return items

    def cleanup(self) -> int:
        self._expiration_queue.remove_expired(remove_callback=self._safe_remove_item)
        return 0

    def _safe_remove_item(self, item: T):
        if self._log_removal:
            logger.debug("Removing {} from expiring set.", item)
        if item in self.contents:
            self.contents.remove(item)
