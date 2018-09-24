import time
from heapq import heappush, heappop

from bxcommon.utils import logger


# Queue for events that take place at some time in the future.
class AlarmQueue(object):
    REMOVED = -1

    def __init__(self):
        # A list of alarm_ids, which contain three things:
        # [fire_time, unique_count, alarm]
        self.alarms = []
        self.uniq_count = 0  # Used for tiebreakers for heap comparison

        # dictionary from fn to a min-heap of scheduled alarms with that function.
        self.approx_alarms_scheduled = {}

    # fn(args) must return 0 if it was successful or a positive integer,
    # WAIT_TIME, to be rescheduled at a delay of WAIT_TIME in the future.
    def register_alarm(self, fire_delay, fn, *args):
        if fire_delay < 0:
            raise ValueError("Invalid negative fire delay.")
        elif fn is None:
            raise ValueError("Fire delay cannot be None.")
        alarm = Alarm(fn, *args)
        alarm_id = [time.time() + fire_delay, self.uniq_count, alarm]
        heappush(self.alarms, alarm_id)
        self.uniq_count += 1
        return alarm_id

    # Register an alarm that will fire sometime between fire_delay +/- slop seconds from now.
    # If such an alarm exists (as told by the memory location of fn) already,
    def register_approx_alarm(self, fire_delay, slop, fn, *args):
        if fire_delay < 0:
            raise ValueError("Invalid negative fire delay.")
        elif fn is None:
            raise ValueError("Fire delay cannot be None.")
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
        if alarm_id is None:
            raise ValueError("Alarm id cannot be none.")
        alarm_id[-1] = AlarmQueue.REMOVED

        # Remove unnecessary alarms from the queue.
        while self.alarms and self.alarms[0][-1] == AlarmQueue.REMOVED:
            heappop(self.alarms)

    def fire_alarms(self):
        if not self.alarms:  # Nothing to do
            return

        curr_time = time.time()
        while self.alarms and self.alarms[0][0] <= curr_time:
            alarm_id = heappop(self.alarms)
            alarm = alarm_id[-1]

            if alarm != AlarmQueue.REMOVED:
                next_delay = alarm.fire()

                # Event wants to be rescheduled.
                if next_delay > 0:
                    alarm_id[0] = time.time() + next_delay
                    heappush(self.alarms, alarm_id)
                # Delete alarm from approx_alarms_scheduled (if applicable)
                elif alarm.fn in self.approx_alarms_scheduled:
                    alarm_heap = self.approx_alarms_scheduled[alarm.fn]

                    # Assert that the alarm that was just fired is the first one in the list
                    assert alarm_heap[0][1] == alarm_id[1]
                    heappop(alarm_heap)

                    if not alarm_heap:
                        del self.approx_alarms_scheduled[alarm.fn]

            elif alarm != AlarmQueue.REMOVED and alarm.fn in self.approx_alarms_scheduled:
                alarm_heap = self.approx_alarms_scheduled[alarm.fn]
                # Since the heap is a min-heap by alarm fire time, then the first
                # alarm should be the one that was just fired.
                assert alarm_heap[0][1] == alarm_id[1]

                heappop(alarm_heap)

    # Return tuple indicating <alarm queue empty, timeout>
    def time_to_next_alarm(self):
        if not self.alarms:
            return True, None  # Nothing to do

        time_to_alarm = self.alarms[0][0] - time.time()

        return False, time_to_alarm

    # Fires all alarms that have timed out on alarm_queue.
    # If the sender knows that some alarm will fire, then they can set has_alarm to be True.
    # Returns the timeout to the next alarm, -1 if there are no new alarms.
    def fire_ready_alarms(self, has_alarm):
        alarmq_empty, time_to_next_alarm = self.time_to_next_alarm()

        if has_alarm or (not alarmq_empty and time_to_next_alarm <= 0):
            # logger.debug("AlarmQueue.fire_ready_alarms", "A timeout occurred")
            while not alarmq_empty and time_to_next_alarm <= 0:
                self.fire_alarms()
                alarmq_empty, time_to_next_alarm = self.time_to_next_alarm()

        return time_to_next_alarm


# An alarm object
class Alarm(object):
    def __init__(self, fn, *args):
        if fn is None:
            raise ValueError("Alarm callback cannot be none.")
        self.fn = fn
        self.args = args

    def fire(self):
        logger.debug("Firing function {0} with args {1}".format(self.fn, self.args))
        return self.fn(*self.args)
