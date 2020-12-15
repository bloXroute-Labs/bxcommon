from typing import TypeVar, Generic, Optional, Dict

from bxcommon.utils.alarm_queue import AlarmQueue
from bxcommon.utils.expiration_queue import ExpirationQueue

KT = TypeVar("KT")
VT = TypeVar("VT")


class ExpiringDict(Generic[KT, VT]):
    """
    Dictionary with expiration time.
    """

    contents: Dict[KT, VT]
    _alarm_queue: AlarmQueue
    _expiration_queue: ExpirationQueue[KT]
    _expiration_time: int
    _name: str

    def __init__(self, alarm_queue: AlarmQueue, expiration_time_s: int, name: str) -> None:
        self.contents = {}
        self._alarm_queue = alarm_queue
        self._expiration_queue = ExpirationQueue(expiration_time_s)
        self._expiration_time = expiration_time_s
        self._name = name

    def __contains__(self, item: KT):
        return item in self.contents

    def __setitem__(self, key: KT, value: VT):
        if key in self.contents:
            self.contents[key] = value
        else:
            self.add(key, value)

    def __delitem__(self, key: KT):
        del self.contents[key]
        self._expiration_queue.remove(key)

    def __getitem__(self, item: KT) -> VT:
        return self.contents[item]

    def add(self, key: KT, value: VT) -> None:
        self.contents[key] = value
        self._expiration_queue.add(key)
        self._alarm_queue.register_approx_alarm(
            self._expiration_time * 2,
            self._expiration_time,
            self.cleanup,
            alarm_name=f"ExpiringDict[{self._name}]#cleanup"
        )

    def cleanup(self) -> float:
        self._expiration_queue.remove_expired(remove_callback=self.remove_item)
        return 0

    def remove_item(self, key: KT) -> Optional[VT]:
        if key in self.contents:
            return self.contents.pop(key)
        else:
            return None
