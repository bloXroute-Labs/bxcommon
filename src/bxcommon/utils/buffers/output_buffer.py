import time
from collections import deque
from typing import Set, Optional

from bxcommon import constants
from bxcommon.utils import memory_utils
from bxcommon.utils.memory_utils import SpecialMemoryProperties, SpecialTuple
from bxutils import logging

logger = logging.get_logger(__name__)


class OutputBuffer(SpecialMemoryProperties):
    """
    There are three key functions on the outputbuffer read interface. This should also
    be implemented by the cut through sink interface.
      - has_more_bytes(): Whether or not there are more bytes in this buffer.
      - get_buffer(): some bytes to send in the outputbuffer
      - advance_buffer(): Advances the buffer by some number of bytes
    """
    EMPTY = memoryview(bytearray(0))  # The empty outputbuffer

    def __init__(self, min_size=None, max_hold_time=None, enable_buffering=False) -> None:
        if min_size is None:
            min_size = constants.OUTPUT_BUFFER_MIN_SIZE
        if max_hold_time is None:
            max_hold_time = constants.OUTPUT_BUFFER_BATCH_MAX_HOLD_TIME

        self.enable_buffering = enable_buffering

        # A deque of memoryview objects representing the raw memoryviews of the messages
        # that are being sent on the outputbuffer.
        self.output_msgs = deque()

        # Offset into the first message of the output_msgs
        self.index = 0

        # The total sum of all of the messages in the outputbuffer
        self.length = 0

        self.min_size = min_size
        # how long we hold onto messages for batching in seconds
        self.max_hold_time = max_hold_time
        self.last_memview = None
        self.last_bytearray: Optional[bytearray] = None
        # size of the last valid memoryview
        self.valid_len = 0
        self.last_bytearray_create_time = None

    def __len__(self):
        return self.length

    def get_buffer(self):
        """
        Gets a non-empty memoryview buffer
        :return: top output message on buffer
        """
        now = time.time()

        if self.enable_buffering and \
                self.last_bytearray is not None and \
                now - self.last_bytearray_create_time >= self.max_hold_time:
            self.flush()

        if not self.output_msgs:
            return OutputBuffer.EMPTY

        return memoryview(self.output_msgs[0])[self.index:]

    def advance_buffer(self, num_bytes: int):
        if num_bytes < 0:
            raise ValueError("Num_bytes must be a positive integer.")

        if (not self.output_msgs and num_bytes > 0) or (self.index + num_bytes) > len(self.output_msgs[0]):
            if self.output_msgs:
                output_message = self.output_msgs[0].tobytes().hex()
            else:
                output_message = None
            raise ValueError(
                "Index cannot be larger than length of first message. Message: {}, Index: {}, Bytes: {}".format(
                    output_message, self.index, num_bytes)
            )

        self.index += num_bytes
        self.length -= num_bytes

        if self.index == len(self.output_msgs[0]):
            self.output_msgs.popleft()
            self.index = 0

    def at_msg_boundary(self):
        return self.index == 0

    def enqueue_msgbytes(self, msg_bytes):
        if not isinstance(msg_bytes, (bytearray, memoryview)):
            raise ValueError("Msg_bytes must be a bytearray. The type given was a {}".format(type(msg_bytes)))

        length = len(msg_bytes)

        if not self.enable_buffering:
            self.output_msgs.append(msg_bytes)
        elif length + self.valid_len > self.min_size:
            if self.last_bytearray is not None:
                self.flush()
            self.output_msgs.append(msg_bytes)
        else:
            now = time.time()
            if self.last_bytearray is None:
                self.last_bytearray = bytearray(self.min_size)
                self.last_memview = memoryview(self.last_bytearray)
                self.last_bytearray[:length] = msg_bytes
                self.valid_len = length
                self.last_bytearray_create_time = now
            else:
                if self.last_bytearray_create_time is None:
                    raise ValueError("last_bytearray_create_time cannot be None")
                self.last_bytearray[self.valid_len:self.valid_len + length] = msg_bytes
                self.valid_len += length

                if now - self.last_bytearray_create_time > self.max_hold_time:
                    self.flush()

        self.length += len(msg_bytes)

    def prepend_msgbytes(self, msg_bytes):
        if not isinstance(msg_bytes, (bytearray, memoryview)):
            raise ValueError("Msg_bytes must be a bytearray.")

        if self.index == 0:
            self.output_msgs.appendleft(msg_bytes)
        else:
            prev_msg = self.output_msgs.popleft()
            self.output_msgs.appendleft(msg_bytes)
            self.output_msgs.appendleft(prev_msg)

        self.length += len(msg_bytes)

    def has_more_bytes(self):
        return self.length != 0

    # TODO: @soumya this is called every 200ms. This needs some future cleanup; possibly in the alarm data structure.
    # Consult Nagle algorithm before implementing improvements.
    def flush(self):
        if self.last_bytearray is None:
            return

        self.output_msgs.append(self.last_memview[:self.valid_len])
        self.last_bytearray_create_time = None
        self.last_bytearray = None
        self.last_memview = None
        self.valid_len = 0

    def safe_empty(self):
        """
        Removes all bytes in OutputBuffer that are not in the current message boundary.
        """
        self.flush()
        if self.output_msgs and self.index:
            first = self.output_msgs.popleft()
            self.output_msgs.clear()
            self.output_msgs.append(first)
            self.length = len(first) - self.index
        else:
            self.output_msgs.clear()
            self.length = 0

    def special_memory_size(self, ids: Optional[Set[int]] = None) -> SpecialTuple:
        return memory_utils.get_special_size(self.output_msgs, ids=ids)
