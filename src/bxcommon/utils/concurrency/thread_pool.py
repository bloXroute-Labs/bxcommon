import functools
import threading
from collections import deque
from concurrent.futures import Future
from threading import Thread, Condition, RLock
from typing import List, Callable, Any, NamedTuple, Deque, Optional


from bxutils import logging

logger = logging.get_logger(__name__)


class WorkItem(NamedTuple):
    callback: Callable
    future: Future


def handle_work_item(work_item: Optional[WorkItem]) -> None:
    if work_item is not None and not work_item.future.cancelled():
        try:
            result = work_item.callback()
        except BaseException as e:
            work_item.future.set_exception(e)
        else:
            try:
                work_item.future.set_result(result)
            # pylint: disable=broad-except
            except Exception as e:
                logger.exception(
                    "{} - unhandled error: {}, failed to set task result {}",
                    threading.current_thread().name,
                    e,
                    result
                )


class ThreadPool:

    def __init__(self, workers: int, thread_name_prefix: str) -> None:
        self._workers = workers
        self._stop_requested = False
        self._threads: List[Thread] = []
        self._work_items: Deque[WorkItem] = deque()
        self._condition = Condition(RLock())
        self._started = False
        for idx in range(self._workers):
            thread = Thread(name="{}-{}".format(thread_name_prefix, idx), target=self._thread_loop)
            thread.daemon = True
            self._threads.append(thread)

    def __enter__(self):
        if not self._started:
            self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def start(self) -> None:
        for thread in self._threads:
            thread.start()
        self._started = True

    def stop(self) -> None:
        with self._condition:
            self._stop_requested = True
            self._condition.notify_all()

    def close(self) -> None:
        if not self._stop_requested:
            self.stop()
        if self._started:
            for thread in self._threads:
                thread.join()
        while self._work_items:
            handle_work_item(self._work_items.popleft())

    def submit(self, callback: Callable[..., Any], *args, **kwargs) -> Future:
        if not self._started:
            raise RuntimeError("Thread pool was never started!")
        future = Future()
        work_item = WorkItem(functools.partial(callback, *args, **kwargs), future)
        with self._condition:
            self._work_items.append(work_item)
            self._condition.notify(1)
        return future

    def _thread_loop(self) -> None:
        try:
            while not self._stop_requested:
                work_item = None
                with self._condition:
                    if len(self._work_items) == 0:
                        self._condition.wait()
                    if self._work_items:
                        work_item = self._work_items.popleft()
                handle_work_item(work_item)
        # pylint: disable=broad-except
        except Exception as e:
            logger.fatal(
                "{} - unhandled error: {}, raised during thread execution!",
                threading.current_thread().name,
                e
            )
