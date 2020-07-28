import functools
from concurrent.futures import Future, CancelledError
from typing import Callable, Any, Optional

from bxcommon import constants
from bxcommon.utils.alarm_queue import AlarmQueue
from bxcommon.utils.concurrency.thread_pool import ThreadPool
from bxutils import log_messages
from bxutils import logging

logger = logging.get_logger(__name__)


class ThreadedRequestService:
    """
    Single point for threaded requests with associated alarms
    """
    thread_pool: ThreadPool

    def __init__(self, name_prefix: str, alarm_queue: AlarmQueue, timeout: int) -> None:
        """
        :param alarm_queue: taken from the node that is using the http service
        :param timeout: timeout for the alarm.
        """
        self.alarm_queue = alarm_queue
        self.thread_pool = ThreadPool(
            constants.THREAD_POOL_WORKER_COUNT, "{}_threaded_request_service".format(name_prefix)
        )
        self.timeout = timeout

    def start(self) -> None:
        self.thread_pool.start()

    def close(self) -> None:
        self.thread_pool.stop()
        self.thread_pool.close()

    def send_threaded_request(
        self,
        request: Callable[..., Any],
        *args: Any,
        done_callback: Optional[Callable[[Future], Any]] = None
    ) -> Future:
        """
        Submit a function to be executed in a separate thread in a thread pool,
        and set up an alarm to verify the correct result of the function

        :param request: function that we need to execute in a separate thread
        :param args: list of arguments for the function
        :param done_callback: Callback when the future is done
        """
        logger.trace("Starting thread for request.")
        task = self.thread_pool.submit(request, *args)
        if done_callback:
            main_thread_callback = functools.partial(
                self.alarm_queue.register_alarm, 0, done_callback
            )
            task.add_done_callback(main_thread_callback)

        self.alarm_queue.register_alarm(
            self.timeout,
            self._threaded_post_alarm,
            task,
            request,
            *args,
            alarm_name=f"threaded_status_check: {str(done_callback)}"
        )
        return task

    def _threaded_post_alarm(self, task: Future, request: Callable[..., None], *args: Any) -> None:
        """
        Callback for the alarm queue.
        Check result of the future task and print a log in case something went wrong
        :param task: future task returned by the thread pool executor
        """
        extra_info = "{}, {}".format(request, args)
        if not task.done():
            if task.running():
                logger.warning(log_messages.THREADED_REQUEST_HAS_LONG_RUNTIME, self.timeout, extra_info)
            else:
                logger.warning(log_messages.THREADED_REQUEST_IS_STALE, extra_info)
                task.cancel()
        else:
            try:
                result = task.result()
                logger.trace("Task {} completed with result: {}", extra_info, result)
            except CancelledError as e:
                logger.error(log_messages.TASK_CANCELLED, task, extra_info, e, exc_info=True)
            except Exception as e:  # pylint: disable=broad-except
                logger.error(log_messages.TASK_FAILED, task, extra_info, e, exc_info=True)
