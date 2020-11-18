import time
from heapq import heappop, heappush
from threading import RLock
from typing import List, Optional, Callable, Dict

from bxcommon import constants
from bxcommon.utils import performance_utils
from bxutils import logging
from bxutils.logging import LogRecordType

logger = logging.get_logger(__name__)
alarm_troubleshooting_logger = logging.get_logger(LogRecordType.AlarmTroubleshooting, __name__)


class Alarm:
    """
    Alarm object. Encapsulates function and arguments.
    """

    def __init__(
        self, fn: Callable, fire_time: float, *args, name: Optional[str] = None, **kwargs
    ):
        if name is None:
            if hasattr(fn, "im_class"):
                cls = getattr(fn, "im_class")
                name = f"{cls}#{fn.__name__}"

            else:
                name = fn.__name__

        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.fire_time = fire_time
        self.name = name

    def fire(self):
        time_from_expected = time.time() - self.fire_time
        if time_from_expected > constants.WARN_ALARM_EXECUTION_OFFSET:
            logger.debug("{} executed {} seconds later than expected.", self, time_from_expected)
        return self.fn(*self.args, **self.kwargs)

    def __repr__(self):
        return f"Alarm<function: {self.name}, fire_time: {self.fire_time}"


class AlarmId:
    fire_time: float
    count: int
    alarm: Alarm
    is_active: bool

    def __init__(self, fire_time: float, count: int, alarm: Alarm) -> None:
        self.fire_time = fire_time
        self.count = count
        self.alarm = alarm
        self.is_active = True

    def __repr__(self):
        return (
            f"AlarmId<"
            f"fire_time: {self.fire_time}, "
            f"count: {self.count}, "
            f"active: {self.is_active}, "
            f"alarm: {self.alarm}"
            f">"
        )

    def __lt__(self, other):
        if not isinstance(other, AlarmId):
            raise TypeError("< not supported between instances of 'AlarmId' and {}".format(other))

        return self.fire_time < other.fire_time or (self.fire_time == other.fire_time and self.count < other.count)

    def __eq__(self, other):
        if not isinstance(other, AlarmId):
            return False
        return (
            self.fire_time == other.fire_time
            and self.count == other.count
            and self.alarm == other.alarm
            and self.is_active == other.is_active
        )


class AlarmQueue:
    """
    Queue for events that take place some time in the future.

    Constants
    ---------
    REMOVED: canceled alarm id for remove

    Attributes
    ----------
    alarms: list of alarms, denoted by (fire time, unique count, alarm function)
    uniq_count: counter used for tiebreakers in heap comparison if same fire time
    approx_alarms_scheduled: function => min-heap of scheduled alarms. used to ensure multiple alarms
                             with the same function handle are not executed repeatedly
    """

    def __init__(self) -> None:
        self.alarms: List[AlarmId] = []
        self.uniq_count: int = 0
        self.approx_alarms_scheduled: Dict[Callable, List[AlarmId]] = {}
        self.lock = RLock()

    def register_alarm(
        self,
        fire_delay: float,
        fn: Callable,
        *args,
        alarm_name: Optional[str] = None,
        fire_immediately: bool = False,
        **kwargs
    ) -> AlarmId:
        """
        Schedules an alarm to be fired in `fire_delay` seconds. Function must return a positive integer
        to be schedule again in the future.
        :param fire_delay: delay in seconds before firing alarm
        :param fn: function to be fired on delay
        :param alarm_name: optional label for alarm
        :param fire_immediately: fires alarm immediately if delay is 0
        :param args: function arguments
        :return: (fire time, unique count, alarm function)
        """
        try:
            hash(fn)
        except Exception:
            raise ValueError(f"Could not register an unhashable alarm: {fn}")

        if fire_delay < 0:
            raise ValueError("Invalid negative fire delay.")
        if fn is None:
            raise ValueError("Function cannot be None.")

        alarm = Alarm(fn, time.time() + fire_delay, *args, name=alarm_name, **kwargs)
        alarm_id = AlarmId(time.time() + fire_delay, self.uniq_count, alarm)

        if fire_immediately and fire_delay == 0:
            alarm.fire()
            return alarm_id

        with self.lock:
            heappush(self.alarms, alarm_id)
            self.uniq_count += 1
        return alarm_id

    def register_approx_alarm(
        self,
        fire_delay: float,
        slop: float,
        fn: Callable,
        *args,
        alarm_name: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Schedules an alarm that will fire in between `fire_delay` +/- slop seconds. The referenced function
        will only be executed once in that time interval, even if multiple calls to this method are made.
        :param fire_delay: delay in seconds before firing alarm
        :param slop: range during which only once instance of this function may be fire
        :param fn: function to be fired
        :param args: function arguments
        :param alarm_name: name of alarm for logging
        """
        try:
            hash(fn)
        except Exception:
            raise ValueError(f"Could not register an unhashable alarm: {fn}")

        if fire_delay < 0:
            raise ValueError("Invalid negative fire delay.")
        if slop < 0:
            raise ValueError("Invalid negative slop.")

        with self.lock:
            if fn not in self.approx_alarms_scheduled:
                new_alarm_id = self.register_alarm(
                    fire_delay, fn, *args, alarm_name=alarm_name, **kwargs
                )
                self.approx_alarms_scheduled[fn] = []
                heappush(self.approx_alarms_scheduled[fn], new_alarm_id)
            else:
                now = time.time()
                late_time, early_time = fire_delay + now + slop, fire_delay + now - slop
                for alarm_id in self.approx_alarms_scheduled[fn]:
                    if early_time <= alarm_id.fire_time <= late_time:
                        return
                heappush(
                    self.approx_alarms_scheduled[fn],
                    self.register_alarm(fire_delay, fn, *args, alarm_name=alarm_name, **kwargs)
                )

    def unregister_alarm(self, alarm_id: AlarmId) -> None:
        """
        Cancels alarm and cleans up the head of the heap.
        :param alarm_id: alarm to cancel
        """
        alarm_id.is_active = False

        with self.lock:
            while self.alarms and not self.alarms[0].is_active:
                heappop(self.alarms)

    def fire_alarms(self) -> None:
        """
        Fire alarms that are ready.
        Reschedules alarms that return a value > 0 with the return value as the next timeout.
        """
        if not self.alarms:
            return

        curr_time = time.time()
        alarms_count = 0

        with self.lock:
            while self.alarms and self.alarms[0].fire_time <= curr_time:
                alarm_id: AlarmId = heappop(self.alarms)
                alarm = alarm_id.alarm

                if alarm_id.is_active:
                    try:
                        start_time = time.time()
                        next_delay = alarm.fire()
                        alarms_count += 1
                    # pylint: disable=broad-except
                    except Exception as e:
                        logger.exception("Alarm {} could not fire and failed with exception: {}", alarm, e)
                        if alarm.fn in self.approx_alarms_scheduled:
                            self._pop_and_cleanup_approx_alarm(alarm_id)
                    else:
                        performance_utils.log_operation_duration(
                            alarm_troubleshooting_logger,
                            "Single alarm", start_time,
                            constants.WARN_ALARM_EXECUTION_DURATION,
                            alarm=alarm
                        )

                        if next_delay is not None and next_delay > 0:
                            next_time = time.time() + next_delay
                            alarm_id.fire_time = next_time
                            alarm_id.alarm.fire_time = next_time
                            heappush(self.alarms, alarm_id)
                        # Delete alarm from approx_alarms_scheduled if applicable
                        elif alarm.fn in self.approx_alarms_scheduled:
                            self._pop_and_cleanup_approx_alarm(alarm_id)

        performance_utils.log_operation_duration(
            alarm_troubleshooting_logger,
            "Alarms",
            curr_time,
            constants.WARN_ALL_ALARMS_EXECUTION_DURATION,
            count=alarms_count
        )

    def fire_ready_alarms(self) -> Optional[float]:
        """
        Fires ready alarm repeatedly until no more should be fired.
        :return: time until next alarm, or None
        """
        time_to_next_alarm = self.time_to_next_alarm()

        while time_to_next_alarm is not None and time_to_next_alarm <= 0:
            self.fire_alarms()
            time_to_next_alarm = self.time_to_next_alarm()

        return time_to_next_alarm

    def time_to_next_alarm(self) -> Optional[float]:
        """
        Indicates if there's not an alarm on the queue and the timeout to the next one if there is.
        :return: (if alarm queue is empty, timeout to next alarm)
        """
        with self.lock:
            if not self.alarms:
                return None

            time_to_alarm = self.alarms[0].fire_time - time.time()
            return time_to_alarm

    def _pop_and_cleanup_approx_alarm(self, alarm_id: AlarmId) -> None:
        alarm_heap = self.approx_alarms_scheduled[alarm_id.alarm.fn]

        # alarm that was just fired must be the first one in the list
        assert alarm_heap[0].count == alarm_id.count
        heappop(alarm_heap)

        if not alarm_heap:
            del self.approx_alarms_scheduled[alarm_id.alarm.fn]
