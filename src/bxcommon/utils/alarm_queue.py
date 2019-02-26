import time
from heapq import heappop, heappush

from bxcommon import constants
from bxcommon.utils import logger


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
    REMOVED = -1

    def __init__(self):
        self.alarms = []
        self.uniq_count = 0
        self.approx_alarms_scheduled = {}

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
        alarm_id = [time.time() + fire_delay, self.uniq_count, alarm]
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

        if fn not in self.approx_alarms_scheduled:
            new_alarm_id = self.register_alarm(fire_delay, fn, *args)
            self.approx_alarms_scheduled[fn] = []
            heappush(self.approx_alarms_scheduled[fn], new_alarm_id)
        else:
            now = time.time()
            late_time, early_time = fire_delay + now + slop, fire_delay + now - slop
            for alarm_id in self.approx_alarms_scheduled[fn]:
                if early_time <= alarm_id[0] <= late_time:
                    return

            heappush(self.approx_alarms_scheduled[fn], self.register_alarm(fire_delay, fn, *args))

    def unregister_alarm(self, alarm_id):
        """
        Cancels alarm and cleans up the head of the heap.
        :param alarm_id: alarm to cancel
        """
        if alarm_id is None:
            raise ValueError("Alarm id cannot be none.")

        alarm_id[-1] = AlarmQueue.REMOVED
        while self.alarms and self.alarms[0][-1] == AlarmQueue.REMOVED:
            heappop(self.alarms)

    def fire_alarms(self):
        """
        Fire alarms that are ready.
        Reschedules alarms that return a value > 0 with the return value as the next timeout.
        """
        if not self.alarms:
            return

        curr_time = time.time()
        while self.alarms and self.alarms[0][0] <= curr_time:
            alarm_id = heappop(self.alarms)
            alarm = alarm_id[-1]

            if alarm != AlarmQueue.REMOVED:

                start_time = time.time()
                next_delay = alarm.fire()
                end_time = time.time()
                if end_time - start_time > constants.WARN_ALARM_EXECUTION_DURATION:
                    logger.warn("{} took {} seconds to execute.".format(alarm, end_time - start_time))

                if next_delay > 0:
                    next_time = time.time() + next_delay
                    alarm_id[0] = next_time
                    alarm_id[-1].fire_time = next_time
                    heappush(self.alarms, alarm_id)
                # Delete alarm from approx_alarms_scheduled if applicable
                elif alarm.fn in self.approx_alarms_scheduled:
                    alarm_heap = self.approx_alarms_scheduled[alarm.fn]

                    # alarm that was just fired must be the first one in the list
                    assert alarm_heap[0][1] == alarm_id[1]
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
        if not self.alarms:
            return True, None

        time_to_alarm = self.alarms[0][0] - time.time()
        return False, time_to_alarm


class Alarm(object):
    """
    Alarm object. Encapsulates function and arguments.
    """

    def __init__(self, fn, fire_time, *args):
        if fn is None:
            raise ValueError("Alarm callback cannot be none.")
        self.fn = fn
        self.args = args
        self.fire_time = fire_time

    def fire(self):
        time_from_expected = time.time() - self.fire_time
        if time_from_expected > constants.WARN_ALARM_EXECUTION_OFFSET:
            logger.warn("{} executed {} seconds later than expected.".format(self, time_from_expected))
        return self.fn(*self.args)

    def get_function_name(self):
        if hasattr(self.fn, "im_class"):
            return "{}#{}".format(self.fn.im_class.__name__, self.fn.__name__)

        else:
            return self.fn.__name__

    def __repr__(self):
        return "Alarm<function: {}, fire_time: {}".format(self.get_function_name(),
                                                          self.fire_time)
