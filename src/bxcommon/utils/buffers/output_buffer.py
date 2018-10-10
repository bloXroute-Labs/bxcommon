from collections import deque


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
        if not isinstance(num_bytes, int) or num_bytes < 0:
            raise ValueError("Num_bytes must be a positive integer.")

        if not self.output_msgs or (self.index + num_bytes) > len(self.output_msgs[0]):
            raise ValueError("Index cannot be larger than length of first message.")

        self.index += num_bytes
        self.length -= num_bytes

        if self.index == len(self.output_msgs[0]):
            self.index = 0
            self.output_msgs.popleft()

    def at_msg_boundary(self):
        return self.index == 0

    def enqueue_msgbytes(self, msg_bytes):
        if not isinstance(msg_bytes, bytearray):
            raise ValueError("Msg_bytes must be a bytearray.")

        self.output_msgs.append(msg_bytes)
        self.length += len(msg_bytes)

    def prepend_msg(self, msg_bytes):
        if not isinstance(msg_bytes, bytearray):
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
