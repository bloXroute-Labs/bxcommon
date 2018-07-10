#
# Copyright (C) 2018, Bloxroute Labs, All rights reserved.
# See the file COPYING for details.
#
# Utility classes
#
import time
from collections import deque
from heapq import *

from bxcommon.util.logger import log_debug


##
# The Inputbuffer Interface
##
class InputBuffer(object):
    def __init__(self):
        self.input_list = deque()
        self.length = 0

    def endswith(self, suffix):
        if self.input_list:
            return False

        if len(self.input_list[-1]) >= len(suffix):
            return self.input_list[-1].endswith(suffix)
        else:
            # FIXME self_input_list, self.suffix are undefined, change
            #   to self.input_list, suffix and test
            raise RuntimeError("FIXME")

        # elif len(self_input_list) > 1:
        #     first_len = len(self.input_list[-1])
        #
        #     return self.suffix[-first_len:] == self.input_list[-1] and \
        #            self.input_list[-2].endswith(self.suffix[:-first_len])
        # return False

    # Adds a bytearray to the end of the input buffer.
    def add_bytes(self, piece):
        assert isinstance(piece, bytearray)
        self.input_list.append(piece)
        self.length += len(piece)

    # Removes the first num_bytes bytes in the input buffer and returns them.
    def remove_bytes(self, num_bytes):
        assert self.length >= num_bytes > 0

        to_return = bytearray(0)
        while self.input_list and num_bytes >= len(self.input_list[0]):
            next_piece = self.input_list.popleft()
            to_return.extend(next_piece)
            num_bytes -= len(next_piece)
            self.length -= len(next_piece)

        assert self.input_list or num_bytes == 0

        if self.input_list:
            to_return.extend(self.input_list[0][:num_bytes])
            self.input_list[0] = self.input_list[0][num_bytes:]
            self.length -= num_bytes

        return to_return

    # Returns the first bytes_to_peek bytes in the input buffer.
    # The assumption is that these bytes are all part of the same message.
    # Thus, we combine pieces if we cannot just return the first message.
    def peek_message(self, bytes_to_peek):
        if bytes_to_peek > self.length:
            return bytearray(0)

        while bytes_to_peek > len(self.input_list[0]):
            head = self.input_list.popleft()
            head.extend(self.input_list.popleft())
            self.input_list.appendleft(head)

        return self.input_list[0]

    # Gets a slice of the inputbuffer from start to end.
    # We assume that this slice is a piece of a single bitcoin message
    # for performance reasons (with respect to the number of copies).
    # Additionally, the start value of the slice must exist.
    def get_slice(self, start, end):
        assert self.length >= start

        # Combine all of the pieces in this slice into the first item on the list.
        # Since we will need to do so anyway when handing the message.
        while end > len(self.input_list[0]) and len(self.input_list) > 1:
            head = self.input_list.popleft()
            head.extend(self.input_list.popleft())
            self.input_list.appendleft(head)

        return self.input_list[0][start:end]


##
# The Outputbuffer Interface ##
##

# There are three key functions on the outputbuffer read interface. This should also
# be implemented by the cut through sink interface.
#   - has_more_bytes(): Whether or not there are more bytes in this buffer.
#   - get_buffer(): some bytes to send in the outputbuffer
#   - advance_buffer(): Advances the buffer by some number of bytes
class OutputBuffer(object):
    EMPTY = bytearray(0)  # The empty outputbuffer

    def __init__(self):
        # A deque of memoryview objects representing the raw memoryviews of the messages
        # that are being sent on the outputbuffer.
        self.output_msgs = deque()

        # Offset into the first message of the output_msgs
        self.index = 0

        # The total sum of all of the messages in the outputbuffer
        self.length = 0

    # Gets a non-empty memoryview buffer
    def get_buffer(self):
        if not self.output_msgs:
            raise RuntimeError("FIXME")
            # FIXME Output buffer is undefined, change to outbuffer, test
            # return OutputBufffer.EMPTY

        return self.output_msgs[0][self.index:]

    def advance_buffer(self, num_bytes):
        self.index += num_bytes
        self.length -= num_bytes

        assert self.index <= len(self.output_msgs[0])

        if self.index == len(self.output_msgs[0]):
            self.index = 0
            self.output_msgs.popleft()

    def at_msg_boundary(self):
        return self.index == 0

    def enqueue_msgbytes(self, msg_bytes):
        self.output_msgs.append(msg_bytes)
        self.length += len(msg_bytes)

    def prepend_msg(self, msg_bytes):
        if self.index == 0:
            self.output_msgs.appendleft(msg_bytes)
        else:
            prev_msg = self.output_msgs.popleft()
            self.output_msgs.appendleft(msg_bytes)
            self.output_msgs.appendleft(prev_msg)

        self.length += len(msg_bytes)

    def has_more_bytes(self):
        return self.length != 0


##
# The Alarm Interface
##

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
        alarm = Alarm(fn, *args)
        alarm_id = [time.time() + fire_delay, self.uniq_count, alarm]
        heappush(self.alarms, alarm_id)
        self.uniq_count += 1
        return alarm_id

    # Register an alarm that will fire sometime between fire_delay +/- slop seconds from now.
    # If such an alarm exists (as told by the memory location of fn) already,
    def register_approx_alarm(self, fire_delay, slop, fn, *args):
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
        alarm_id[-1] = AlarmQueue.REMOVED

        # Remove unnecessary alarms from the queue.
        while self.alarms[0][-1] == AlarmQueue.REMOVED:
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
            return True, -1  # Nothing to do
        return False, self.alarms[0][0] - time.time()

    # Fires all alarms that have timed out on alarm_queue.
    # If the sender knows that some alarm will fire, then they can set has_alarm to be True.
    # Returns the timeout to the next alarm, -1 if there are no new alarms.
    def fire_ready_alarms(self, has_alarm):
        alarmq_empty, time_to_next_alarm = self.time_to_next_alarm()
        if has_alarm or (not alarmq_empty and time_to_next_alarm <= 0):
            # log_debug("AlarmQueue.fire_ready_alarms", "A timeout occurred")
            while not alarmq_empty and time_to_next_alarm <= 0:
                self.fire_alarms()
                alarmq_empty, time_to_next_alarm = self.time_to_next_alarm()

        return time_to_next_alarm


# An alarm object
class Alarm(object):
    def __init__(self, fn, *args):
        self.fn = fn
        self.args = args

    def fire(self):
        log_debug("Firing function {0} with args {1}".format(self.fn, self.args))
        return self.fn(*self.args)
