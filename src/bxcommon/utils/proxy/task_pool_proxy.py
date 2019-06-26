import time
import task_pool_executor as tpe  # pyre-ignore for now, figure this out later (stub file or Python wrapper?)


_executor: tpe.TaskPoolExecutor = None


def init(thread_pool_parallelism_degree: int):
    global _executor
    _executor = tpe.TaskPoolExecutor()
    _executor.init(thread_pool_parallelism_degree)


# TODO : convert to async
def run_task(tsk: tpe.MainTaskBase):
    _executor.enqueue_task(tsk)
    while not tsk.is_completed():
        time.sleep(0)
        continue
    tsk.assert_execution()


def get_pool_size() -> int:
    return _executor.size()
