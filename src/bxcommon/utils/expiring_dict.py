from typing import TypeVar, Generic, Optional, Dict

from bxcommon.utils.alarm_queue import AlarmQueue
from bxcommon.utils.expiration_queue import ExpirationQueue

KT = TypeVar("KT")
VT = TypeVar("VT")


class ExpiringDict(Generic[KT, VT]):
    """
    Set with expiration time.

    For determining if items are in the set, use "if item in expiring_set.contents".
    __contains__ is intentionally not overwritten. This is a performance critical class,
    and we're avoiding extra function call overhead.
    """

    contents: Dict[KT, VT]
    _alarm_queue: AlarmQueue
    _expiration_queue: ExpirationQueue[KT]
    _expiration_time: int

    def __init__(self, alarm_queue, expiration_time_s):
        self.contents = {}
        self._alarm_queue = alarm_queue
        self._expiration_queue = ExpirationQueue(expiration_time_s)
        self._expiration_time = expiration_time_s

    def add(self, key, value):
        self.contents[key] = value
        self._expiration_queue.add(key)
        self._alarm_queue.register_approx_alarm(self._expiration_time * 2, self._expiration_time, self.cleanup)

    def cleanup(self):
        self._expiration_queue.remove_expired(remove_callback=self.remove_item)
        return 0

    def remove_item(self, key) -> Optional[VT]:
        if key in self.contents:
            return self.contents.pop(key)
        else:
            return None
