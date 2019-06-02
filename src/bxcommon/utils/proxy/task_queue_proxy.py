import typing
from collections import deque
from bxcommon.utils.proxy.task_proxy import TaskProxy
import task_pool_executor as tpe  # pyre-ignore for now, figure this out later (stub file or Python wrapper?)


class TaskQueueProxy:
    QUEUE_GROW_SIZE = 10

    def __init__(
            self, task_creator: typing.Callable[[], tpe.MainTaskBase],
            grow_size: int = QUEUE_GROW_SIZE
    ):
        self._task_creator = task_creator
        self._grow_size = grow_size
        self._queue: typing.Deque[TaskProxy] = deque()
        self._extend_queue()

    def __len__(self) -> int:
        return len(self._queue)

    def borrow_task(self) -> TaskProxy:
        try:
            tsk = self._queue.popleft()
        except IndexError:
            tsk = self._extend_queue()
        return tsk

    def return_task(self, tsk: TaskProxy):
        self._queue.append(tsk)

    def _extend_queue(self) -> TaskProxy:
        tsk = None
        for _ in range(self._grow_size):
            tsk = TaskProxy(self._task_creator())
            self._queue.append(tsk)
        return tsk
