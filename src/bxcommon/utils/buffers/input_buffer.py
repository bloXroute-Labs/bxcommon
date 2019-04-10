from collections import deque


class InputBuffer(object):
    def __init__(self):
        self.input_list = deque()
        self.length = 0

    def endswith(self, suffix):
        if not self.input_list:
            return False

        if not isinstance(suffix, bytearray):
            raise ValueError("Suffix must be a bytearray.")

        return self.input_list[-1].endswith(suffix)

    def add_bytes(self, piece):
        """
        Adds a bytearray to the end of the input buffer.
        """
        if not isinstance(piece, (bytearray, memoryview)):
            raise ValueError("Piece must be a bytearray.")
        self.input_list.append(piece)
        self.length += len(piece)

    def remove_bytes(self, num_bytes):
        """
        Removes the first num_bytes bytes in the input buffer and returns them.
        """
        if num_bytes is None or num_bytes < 0:
            raise ValueError("Invalid num_bytes {}".format(num_bytes))

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

    def peek_message(self, bytes_to_peek):
        """
        Returns at LEAST the first bytes_to_peek bytes in the input buffer.
        The assumption is that these bytes are all part of the same message.
        Thus, we combine pieces if we cannot just return the first message.
        """
        if bytes_to_peek > self.length:
            bytes_to_peek = self.length

        if bytes_to_peek == 0:
            return bytearray(0)

        while bytes_to_peek > len(self.input_list[0]):
            head = self.input_list.popleft()
            head.extend(self.input_list.popleft())
            self.input_list.appendleft(head)

        return self.input_list[0]

    def get_slice(self, start, end):
        """
        Gets a slice of the inputbuffer from start to end.
        We assume that this slice is a piece of a single bitcoin message
        for performance reasons (with respect to the number of copies).
        Additionally, the start value of the slice must exist.
        """
        if start is None or end is None or self.length < start:
            raise ValueError("Start ({}) and end ({}) must exist and start must be less or equal to length ({})."
                             .format(start, end, self.length))

        # Combine all of the pieces in this slice into the first item on the list.
        # Since we will need to do so anyway when handing the message.
        while end > len(self.input_list[0]) and len(self.input_list) > 1:
            head = self.input_list.popleft()
            head.extend(self.input_list.popleft())
            self.input_list.appendleft(head)

        return self.input_list[0][start:end]

    def __len__(self):
        return self.length

    def __getitem__(self, item):
        if not isinstance(item, slice):
            raise ValueError("Input buffer does not support nonslice indexing")

        if item.step is not None and item.step != 1:
            raise ValueError("Input buffer does not support non 1 slice step values")

        start = item.start
        if start is None:
            start = 0

        stop = item.stop
        if stop is None:
            stop = self.length

        return self.get_slice(start, stop)

