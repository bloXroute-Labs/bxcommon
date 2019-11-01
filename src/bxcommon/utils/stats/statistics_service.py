import time
import traceback
from abc import ABCMeta, abstractmethod
from collections import deque
from datetime import datetime
from threading import Thread, Lock

from bxutils import logging
from bxutils.logging.log_level import LogLevel
from bxutils.logging.log_record_type import LogRecordType

from bxcommon import constants


logger = logging.get_logger(__name__)


# TODO replace with dataclass
class StatsIntervalData(object):
    __slots__ = ["node", "node_id", "start_time", "end_time"]

    def __init__(self, node, node_id, start_time=None, end_time=None):
        self.node = node
        self.node_id = node_id
        self.start_time = start_time
        self.end_time = end_time


# TODO: change default log level from STATS to info


class StatisticsService(metaclass=ABCMeta):
    """
    Abstract class of statistics services.
    """

    INTERVAL_DATA_CLASS = StatsIntervalData

    def __init__(self, name, interval=0, look_back=1, reset=False, logger=logger, log_level=LogLevel.STATS):
        self.history = deque(maxlen=look_back)
        self.node = None
        self.name = name
        self.log_level = log_level
        self.logger = logger
        self.interval_data = None
        self.interval = interval
        self.reset = reset

    @abstractmethod
    def get_info(self):
        """
        Constructs response object to be outputted on stat service set interval.
        :return: dictionary to be converted to JSON
        """
        pass

    def set_node(self, node):
        self.node = node
        self.create_interval_data_object()

    def create_interval_data_object(self):
        self.interval_data = self.INTERVAL_DATA_CLASS(self.node, self.node.opts.node_id, datetime.utcnow())

    def close_interval_data(self):
        self.interval_data.end_time = datetime.utcnow()
        self.history.append(self.interval_data)

    def flush_info(self):
        self.close_interval_data()
        self.logger.log(self.log_level, {"data": self.get_info(), "type": self.name})

        # Start a new interval data if non cumulative
        if self.reset:
            self.create_interval_data_object()
        return self.interval


class ThreadedStatisticsService(StatisticsService, metaclass=ABCMeta):
    """
    Abstract class for stats service that may take a long time to execute.
    """

    def __init__(self, name, interval=0, look_back=1, reset=False, logger=None):
        super(ThreadedStatisticsService, self).__init__(name, interval, look_back, reset, logger=logger)
        self._thread = None
        self._alive = True
        self._lock = Lock()

    @abstractmethod
    def get_info(self):
        """
        Constructs response object to be outputted on stat service set interval.
        :return: dictionary to be converted to JSON
        """
        pass

    def start_recording(self, record_fn):
        self._thread = Thread(target=self.loop_record_on_thread, args=(record_fn,))
        self._thread.start()

    def stop_recording(self):
        # TODO: This is necessary in order to make the tests pass. We are initializing multiple
        # nodes in a process in a test, both of which are initializing the memory_statistics_service.
        # Thus, there is unclear ownership of the global variable. The right fix here is to make
        # memory_statistics_service not a singleton anymore and have it be a variable that is assigned
        # on a per-node basis.
        if self._thread is None:
            logger.error(
                "Thread was not initialized yet, but stop_recording was called. An invariant in the code is broken."
            )
            return

        with self._lock:
            self._alive = False

        self._thread.join()

    def sleep_and_check_alive(self, sleep_time):
        """
        Sleeps for sleeptime seconds and checks whether or this service is alive every 30 seconds.
        Returns whether or not this service is alive at the end of this sleep time.
        """

        with self._lock:
            alive = self._alive
        while sleep_time > 0 and alive:
            time.sleep(constants.THREADED_STAT_SLEEP_INTERVAL)
            sleep_time -= constants.THREADED_STAT_SLEEP_INTERVAL
            with self._lock:
                alive = self._alive
        else:
            time.sleep(0)  # ensure sleep is called regardless of the sleep time value
        return alive

    def loop_record_on_thread(self, record_fn):
        """
        Assume that record_fn is a read-only function and its okay to get somewhat stale data.
        """
        alive = self.sleep_and_check_alive(self.interval)
        while alive:
            start_time = time.time()
            try:
                record_fn()
            except Exception as e:
                logger.error("Recording {} stats failed with exception: {}. Stack trace: {}".format(self.name, e,
                                                                                                    traceback.format_exc()))
                runtime = 0
            else:
                runtime = time.time() - start_time
                logger.debug("Recording {} stats took {} seconds".format(self.name, runtime))

            sleep_time = self.interval - runtime
            alive = self.sleep_and_check_alive(sleep_time)
