import typing
from collections import deque
import task_pool_executor as tpe  # pyre-ignore for now, figure this out later (stub file or Python wrapper?)


class TaskQueueProxy:
    QUEUE_GROW_SIZE = 10

    def __init__(
            self, task_creator: typing.Callable[[], tpe.MainTaskBase],
            grow_size: int = QUEUE_GROW_SIZE
    ):
        self._task_creator = task_creator
        self._grow_size = grow_size
        self._queue: typing.Deque[tpe.MainTaskBase] = deque()
        self._extend_queue()

    def __len__(self) -> int:
        return len(self._queue)

    def borrow_task(self) -> tpe.MainTaskBase:   # pyre-ignore
        try:
            tsk = self._queue.popleft()
        except IndexError:
            tsk = self._extend_queue()
        return tsk

    def return_task(self, tsk: tpe.MainTaskBase):
        self._queue.appendleft(tsk)

    def _extend_queue(self) -> tpe.MainTaskBase:  # pyre-ignore
        tsk = None
        for _ in range(self._grow_size):
            tsk = self._task_creator()
            self._queue.append(tsk)
        return tsk
