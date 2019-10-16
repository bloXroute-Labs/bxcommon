import time
from heapq import heappop, heappush
from threading import RLock
from typing import List

from bxcommon import constants
from bxutils import logging

logger = logging.get_logger(__name__)


class Alarm:
    """
    Alarm object. Encapsulates function and arguments.
    """

    def __init__(self, fn, fire_time, *args, **kwargs):
        if fn is None:
            raise ValueError("Alarm callback cannot be none.")
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.fire_time = fire_time

    def fire(self):
        time_from_expected = time.time() - self.fire_time
        if time_from_expected > constants.WARN_ALARM_EXECUTION_OFFSET:
            logger.debug("{} executed {} seconds later than expected.", self, time_from_expected)
        return self.fn(*self.args, **self.kwargs)

    def get_function_name(self):
        if hasattr(self.fn, "im_class"):
            return "{}#{}".format(self.fn.im_class.__name__, self.fn.__name__)

        else:
            return self.fn.__name__

    def __repr__(self):
        return "Alarm<function: {}, fire_time: {}".format(self.get_function_name(),
                                                          self.fire_time)


class AlarmId:
    fire_time: float
    count: int
    alarm: Alarm
    is_active: bool

    def __init__(self, fire_time, count, alarm):
        self.fire_time = fire_time
        self.count = count
        self.alarm = alarm
        self.is_active = True

    def __repr__(self):
        return f"AlarmId<fire_time: {self.fire_time}, count: {self.count}, active: {self.is_active}, " \
            f"alarm: {self.alarm}>"

    def __lt__(self, other):
        if not isinstance(other, AlarmId):
            raise TypeError("< not supported between instances of 'AlarmId' and {}".format(other))

        return self.fire_time < other.fire_time or (self.fire_time == other.fire_time and self.count < other.count)

    def __eq__(self, other):
        if not isinstance(other, AlarmId):
            return False
        return self.fire_time == other.fire_time and self.count == other.count and self.alarm == other.alarm \
               and self.is_active == other.is_active


class AlarmQueue(object):
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

    def __init__(self):
        self.alarms: List[AlarmId] = []
        self.uniq_count = 0
        self.approx_alarms_scheduled = {}
        self.lock = RLock()

    def register_alarm(self, fire_delay, fn, *args):
        """
        Schedules an alarm to be fired in `fire_delay` seconds. Function must return a positive integer
        to be schedule again in the future.
        :param fire_delay: delay in seconds before firing alarm
        :param fn: function to be fired on delay
        :param args: function arguments
        :return: (fire time, unique count, alarm function)
        """
        if fire_delay < 0:
            raise ValueError("Invalid negative fire delay.")
        elif fn is None:
            raise ValueError("Function cannot be None.")

        alarm = Alarm(fn, time.time() + fire_delay, *args)
        alarm_id = AlarmId(time.time() + fire_delay, self.uniq_count, alarm)
        with self.lock:
            heappush(self.alarms, alarm_id)
            self.uniq_count += 1
        return alarm_id

    def register_approx_alarm(self, fire_delay, slop, fn, *args):
        """
        Schedules an alarm that will fire in between `fire_delay` +/- slop seconds. The referenced function
        will only be executed once in that time interval, even if multiple calls to this method are made.
        :param fire_delay: delay in seconds before firing alarm
        :param slop: range during which only once instance of this function may be fire
        :param fn: function to be fired
        :param args: function arguments
        """
        if fire_delay < 0:
            raise ValueError("Invalid negative fire delay.")
        elif fn is None:
            raise ValueError("Function cannot be None.")
        elif slop < 0:
            raise ValueError("Invalid negative slop.")

        with self.lock:
            if fn not in self.approx_alarms_scheduled:
                new_alarm_id = self.register_alarm(fire_delay, fn, *args)
                self.approx_alarms_scheduled[fn] = []
                heappush(self.approx_alarms_scheduled[fn], new_alarm_id)
            else:
                now = time.time()
                late_time, early_time = fire_delay + now + slop, fire_delay + now - slop
                for alarm_id in self.approx_alarms_scheduled[fn]:
                    if early_time <= alarm_id.fire_time <= late_time:
                        return
                heappush(self.approx_alarms_scheduled[fn], self.register_alarm(fire_delay, fn, *args))

    def unregister_alarm(self, alarm_id: AlarmId):
        """
        Cancels alarm and cleans up the head of the heap.
        :param alarm_id: alarm to cancel
        """
        if alarm_id is None:
            raise ValueError("Alarm id cannot be none.")

        alarm_id.is_active = False

        with self.lock:
            while self.alarms and not self.alarms[0].is_active:
                heappop(self.alarms)

    def fire_alarms(self):
        """
        Fire alarms that are ready.
        Reschedules alarms that return a value > 0 with the return value as the next timeout.
        """
        if not self.alarms:
            return

        curr_time = time.time()

        with self.lock:
            while self.alarms and self.alarms[0].fire_time <= curr_time:
                alarm_id: AlarmId = heappop(self.alarms)
                alarm = alarm_id.alarm

                if alarm_id.is_active:
                    try:
                        start_time = time.time()
                        next_delay = alarm.fire()
                        end_time = time.time()
                    except Exception as e:
                        logger.exception("Alarm {} could not fire and failed with exception: {}", alarm, e)
                    else:
                        if end_time - start_time > constants.WARN_ALARM_EXECUTION_DURATION:
                            logger.debug("{} took {} seconds to execute.", alarm, end_time - start_time)

                        if next_delay is not None and next_delay > 0:
                            next_time = time.time() + next_delay
                            alarm_id.fire_time = next_time
                            alarm_id.alarm.fire_time = next_time
                            heappush(self.alarms, alarm_id)
                        # Delete alarm from approx_alarms_scheduled if applicable
                        elif alarm.fn in self.approx_alarms_scheduled:
                            alarm_heap = self.approx_alarms_scheduled[alarm.fn]

                            # alarm that was just fired must be the first one in the list
                            assert alarm_heap[0].count == alarm_id.count
                            heappop(alarm_heap)

                            if not alarm_heap:
                                del self.approx_alarms_scheduled[alarm.fn]

    def fire_ready_alarms(self, has_alarm):
        """
        Fires ready alarm repeatedly until no more should be fired.
        :param has_alarm: Force fire initial alarm. (what?)
        :return: time until next alarm, or None
        """
        alarmq_empty, time_to_next_alarm = self.time_to_next_alarm()

        if has_alarm or (not alarmq_empty and time_to_next_alarm <= 0):
            while not alarmq_empty and time_to_next_alarm <= 0:
                self.fire_alarms()
                alarmq_empty, time_to_next_alarm = self.time_to_next_alarm()

        return time_to_next_alarm

    def time_to_next_alarm(self):
        """
        Indicates if there's not an alarm on the queue and the timeout to the next one if there is.
        :return: (if alarm queue is empty, timeout to next alarm)
        """
        with self.lock:
            if not self.alarms:
                return True, None

            time_to_alarm = self.alarms[0].fire_time - time.time()
            return False, time_to_alarm
