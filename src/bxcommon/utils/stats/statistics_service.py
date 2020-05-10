import time
import traceback
from abc import ABCMeta, abstractmethod
from collections import deque
from datetime import datetime
from threading import Thread, Lock
from typing import Optional, TypeVar, Generic, Deque, Type, Callable, Dict, Any, TYPE_CHECKING

from bxcommon import constants
from bxutils import log_messages
from bxutils import logging
from bxutils.logging import CustomLogger
from bxutils.logging.log_level import LogLevel
from bxutils.logging.log_record_type import LogRecordType

logger = logging.get_logger(__name__)
task_duration_logger = logging.get_logger(LogRecordType.TaskDuration, __name__)

if TYPE_CHECKING:
    # pylint: disable=ungrouped-imports,cyclic-import
    from bxcommon.connections.abstract_node import AbstractNode


class StatsIntervalData:
    node: "AbstractNode"
    node_id: str
    start_time: datetime
    end_time: Optional[datetime]
    _closed: bool

    def __init__(self, node: "AbstractNode", node_id: str):
        self.node = node
        self.node_id = node_id
        self.start_time = datetime.utcnow()
        self.end_time = None

        self._closed = False

    def close(self):
        self.end_time = datetime.utcnow()
        self._closed = True


T = TypeVar("T", bound=StatsIntervalData)
N = TypeVar("N", bound="AbstractNode")


class StatisticsService(Generic[T, N], metaclass=ABCMeta):
    """
    Abstract class of statistics services.
    """
    history: Deque[T]
    node: Optional[N]
    name: str
    log_level: LogLevel
    logger: CustomLogger
    interval_data: Optional[T]
    interval: int
    reset: bool

    def __init__(
        self,
        name: str,
        interval: int = 0,
        look_back: int = 1,
        reset: bool = False,
        stat_logger: CustomLogger = logger,
        log_level: LogLevel = LogLevel.STATS,
    ):
        self.history = deque(maxlen=look_back)
        self.node = None
        self.name = name
        self.log_level = log_level
        self.logger = stat_logger
        self.interval_data = None
        self.interval = interval
        self.reset = reset

    @abstractmethod
    def get_interval_data_class(self) -> Type[T]:
        pass

    @abstractmethod
    def get_info(self) -> Dict[str, Any]:
        """
        Constructs response object to be outputted on stat service set interval.
        :return: dictionary to be converted to JSON
        """

    def set_node(self, node: N) -> None:
        self.node = node
        self.create_interval_data_object()

    def create_interval_data_object(self) -> None:
        assert self.node is not None
        # pyre-fixme[6]: Expected `AbstractNode` for 1st param but got
        #  `Optional[Variable[N (bound to AbstractNode)]]`.
        # pyre-fixme[16]: `Optional` has no attribute `opts`.
        self.interval_data = self.get_interval_data_class()(self.node, self.node.opts.node_id)

    def close_interval_data(self) -> None:
        assert self.node is not None
        assert self.interval_data is not None
        # pyre-fixme[16]: `Optional` has no attribute `close`.
        self.interval_data.close()
        # pyre-fixme[6]: Expected `T` for 1st param but got `Optional[Variable[T
        #  (bound to StatsIntervalData)]]`.
        self.history.append(self.interval_data)

    def flush_info(self) -> int:
        self.close_interval_data()
        self.logger.log(self.log_level, {"data": self.get_info(), "type": self.name})

        # Start a new interval data if non cumulative
        if self.reset:
            self.create_interval_data_object()
        return self.interval


class ThreadedStatisticsService(StatisticsService[T, N], metaclass=ABCMeta):
    """
    Abstract class for stats service that may take a long time to execute.
    """

    _thread: Optional[Thread]
    _alive: bool
    _lock: Lock

    def __init__(self, name: str, *args, **kwargs):
        super(ThreadedStatisticsService, self).__init__(name, *args, **kwargs)
        self._thread = None
        self._alive = True
        self._lock = Lock()

    def start_recording(self, record_fn: Callable) -> None:
        self._thread = Thread(target=self.loop_record_on_thread, args=(record_fn,))
        # pyre-fixme[16]: `Optional` has no attribute `start`.
        self._thread.start()

    def stop_recording(self) -> None:
        # TODO: This is necessary in order to make the tests pass. We are initializing multiple
        # nodes in a process in a test, both of which are initializing the memory_statistics_service.
        # Thus, there is unclear ownership of the global variable. The right fix here is to make
        # memory_statistics_service not a singleton anymore and have it be a variable that is assigned
        # on a per-node basis.
        if self._thread is None:
            self.logger.error(log_messages.STOP_RECORDING_CALLED_ON_UNINITIALIZED_THREAD)
            return

        with self._lock:
            self._alive = False

        # pyre-fixme[16]: `Optional` has no attribute `join`.
        self._thread.join()

    def sleep_and_check_alive(self, sleep_time: float) -> bool:
        """
        Sleeps for sleep_time seconds and checks whether or this service is alive every 30 seconds.
        Returns whether or not this service is alive at the end of this sleep time.
        """

        with self._lock:
            alive = self._alive
        while sleep_time > 0 and alive:
            time.sleep(constants.THREADED_STATS_SLEEP_INTERVAL_S)
            sleep_time -= constants.THREADED_STATS_SLEEP_INTERVAL_S
            with self._lock:
                alive = self._alive

        time.sleep(0)  # ensure sleep is called regardless of the sleep time value
        return alive

    def loop_record_on_thread(self, record_fn: Callable) -> None:
        """
        Assume that record_fn is a read-only function and its okay to get somewhat stale data.
        """
        assert self.node is not None
        alive = self.sleep_and_check_alive(self.interval)
        while alive:
            start_date_time = datetime.utcnow()
            start_time = time.time()
            try:
                record_fn()
            # pylint: disable=broad-except
            except Exception as e:
                self.logger.error(
                    log_messages.FAILURE_RECORDING_STATS, self.name, e, traceback.format_exc()
                )
                runtime = 0
            else:
                runtime = time.time() - start_time
                task_duration_logger.statistics(
                    {
                        "type": "TaskDuration",
                        "start_date_time": start_date_time,
                        "task": self.name,
                        "duration": runtime,
                        # pyre-fixme[16]: `Optional` has no attribute `opts`.
                        "node_id": self.node.opts.node_id,
                    }
                )
            sleep_time = self.interval - runtime
            alive = self.sleep_and_check_alive(sleep_time)
