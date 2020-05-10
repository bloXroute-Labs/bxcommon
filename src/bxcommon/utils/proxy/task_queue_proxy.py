from collections import deque
from typing import Optional, Set, Deque, Callable, TypeVar, Generic

from bxcommon.utils.memory_utils import SpecialMemoryProperties, SpecialTuple

import task_pool_executor as tpe


T = TypeVar("T", bound=tpe.MainTaskBase)


class TaskQueueProxy(Generic[T], SpecialMemoryProperties):
    QUEUE_GROW_SIZE = 1  # TODO: increase this after moving to async task execution

    def __init__(
        self,
        task_creator: Callable[[], T],
        grow_size: int = QUEUE_GROW_SIZE
    ):
        self._task_creator = task_creator
        self._grow_size = grow_size
        self._queue: Deque[T] = deque()
        self._extend_queue()

    def __len__(self) -> int:
        return len(self._queue)

    def borrow_task(self) -> T:
        try:
            tsk = self._queue.popleft()
        except IndexError:
            tsk = self._extend_queue()
        return tsk

    def return_task(self, tsk: T):
        self._queue.appendleft(tsk)

    def special_memory_size(self, ids: Optional[Set[int]] = None) -> SpecialTuple:
        total_size = 0
        if ids is None:
            ids = set()
        for tsk in self._queue:
            total_size += tsk.get_task_byte_size()
        return SpecialTuple(total_size, ids)

    def _extend_queue(self) -> T:
        tsk = None
        for _ in range(self._grow_size):
            tsk = self._task_creator()
            self._queue.append(tsk)

        assert tsk is not None
        return tsk
