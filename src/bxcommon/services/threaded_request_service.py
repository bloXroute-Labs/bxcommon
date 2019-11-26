from concurrent.futures import ThreadPoolExecutor, Future, CancelledError
from typing import Callable, Any
from bxutils import logging
from bxcommon.utils.alarm_queue import AlarmQueue

logger = logging.get_logger(__name__)


class ThreadedRequestService:
    """
    Single point for threaded requests with associated alarms
    """
    _instance = None

    def __new__(cls, alarm_queue: AlarmQueue, timeout: int):
        """
        :param alarm_queue: taken from the node that is using the http service
        :param timeout: timeout for the alarm.
        """
        if cls._instance is None:
            cls._instance = super(ThreadedRequestService, cls).__new__(cls)
            cls._instance.logger = logger
            cls._instance.alarm_queue = alarm_queue
            cls._instance.thread_pool = ThreadPoolExecutor()
            cls._instance.timeout = timeout
        return cls._instance

    def send_threaded_request(self, request: Callable[..., None], *args: Any) -> None:
        """
        Submit a function to be executed in a separate thread in a thread pool,
        and set up an alarm to verify the correct result of the function

        :param request: function that we need to execute in a separate thread
        :param args: list of arguments for the function
        """
        # pyre-ignore
        self.logger.trace("Starting thread for request.")
        # pyre-ignore
        task = self.thread_pool.submit(request, *args)
        # pyre-ignore
        self.alarm_queue.register_alarm(self.timeout, self._threaded_post_alarm, task, request, *args)

    def _threaded_post_alarm(self, task: Future, request: Callable[..., None], *args: Any) -> None:
        """
        Callback for the alarm queue.
        Check result of the future task and print a log in case something went wrong
        :param task: future task returned by the thread pool executor
        """
        extra_info = "{}, {}".format(request, args)
        if not task.done():
            if task.running():
                # pyre-ignore
                self.logger.warning("Threaded request was enqueued more than {} minute(s) ago and hasn't"
                                    " finished yet: {}", self.timeout, extra_info)
            else:
                # pyre-ignore
                self.logger.warning("Threaded request hasn't started running yet, cancelling: {}", extra_info)
                task.cancel()
        else:
            try:
                result = task.result()
                # pyre-ignore
                self.logger.trace("Task {} completed with result: {}", extra_info, result)
            except CancelledError as e:
                # pyre-ignore
                self.logger.error("Task: {} with values: {} was cancelled: {}", task, extra_info, e, exc_info=True)
            except Exception as e:
                # pyre-ignore
                self.logger.error("Task: {} with values: {} failed due to error: {}", task, extra_info, e, exc_info=True)

