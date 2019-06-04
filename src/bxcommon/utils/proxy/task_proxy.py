import time
import task_pool_executor as tpe  # pyre-ignore for now, figure this out later (stub file or Python wrapper?)


class TaskProxy:

    def __init__(self, tsk: tpe.MainTaskBase):
        self.tsk = tsk

    # TODO : convert to async
    def run(self):
        tpe.enqueue_task(self.tsk)
        while not self.tsk.is_completed():
            time.sleep(0)
            continue
        self.tsk.assert_execution()
