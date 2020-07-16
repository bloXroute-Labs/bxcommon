import time
from typing import Optional
import task_pool_executor as tpe

_executor: Optional[tpe.TaskPoolExecutor] = None


def init(thread_pool_parallelism_degree: int) -> None:
    executor = tpe.TaskPoolExecutor()
    executor.init(thread_pool_parallelism_degree)

    # pylint: disable=global-statement
    global _executor
    _executor = executor


# TODO : convert to async
def run_task(tsk: tpe.MainTaskBase) -> None:
    executor = _executor

    assert executor is not None
    executor.enqueue_task(tsk)
    while not tsk.is_completed():
        time.sleep(0)
        continue
    tsk.assert_execution()
    tsk.cleanup()


def get_pool_size() -> int:
    executor = _executor
    assert executor is not None
    return executor.size()
