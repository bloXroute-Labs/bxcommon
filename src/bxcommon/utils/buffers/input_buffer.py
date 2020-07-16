from collections import deque
from typing import Deque, Union
from typing import Set, Optional

from bxcommon.utils import memory_utils
from bxcommon.utils.memory_utils import SpecialMemoryProperties, SpecialTuple


class InputBuffer(SpecialMemoryProperties):
    def __init__(self) -> None:
        self.input_list: Deque[Union[memoryview, bytearray, bytes]] = deque()
        self.length = 0

    def endswith(self, suffix: Union[memoryview, bytearray, bytes]) -> bool:
        if not self.input_list:
            return False

        # pyre-fixme[25]: Assertion will always fail.
        if not isinstance(suffix, (memoryview, bytearray, bytes)):
            raise ValueError(f"Suffix must be memoryview, bytearray or bytes, not {type(suffix)}.")

        end_slice = self.input_list[-1]
        if len(end_slice) < len(suffix):
            end_slice = self.get_slice(self.length - len(suffix), self.length)
        if not isinstance(end_slice, bytearray):
            end_slice = bytearray(end_slice)
            self.input_list[-1] = end_slice

        return end_slice.endswith(suffix)  # pyre-ignore

    def add_bytes(self, piece: Union[bytearray, bytes, memoryview]) -> None:
        """
        Adds a data bytes to the end of the input buffer.
        """
        # pyre-fixme[25]: Assertion will always fail.
        if not isinstance(piece, (bytearray, memoryview, bytes)):
            raise ValueError("Piece must be a bytearray, bytes or memoryview.")
        self.input_list.append(piece)
        self.length += len(piece)

    def remove_bytes(self, num_bytes: int) -> Union[bytearray, bytes, memoryview]:
        """
        Removes the first num_bytes bytes in the input buffer and returns them.
        """
        if num_bytes is None or num_bytes < 0:
            raise ValueError("Invalid num_bytes {}".format(num_bytes))

        self._shrink_if_needed(num_bytes, True)

        assert self.input_list or num_bytes == 0, f"Input buffer is empty and attempting to remove {num_bytes} bytes!"

        if self.input_list and num_bytes > 0:
            to_return = self.input_list[0][:num_bytes]
            self.input_list[0] = self.input_list[0][num_bytes:]
            self.length -= num_bytes
        else:
            to_return = bytearray(0)

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
        self._shrink_if_needed(bytes_to_peek)

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
        self._shrink_if_needed(end)
        return self.input_list[0][start:end]

    def __len__(self) -> int:
        return self.length

    def __getitem__(self, item) -> Union[memoryview, bytearray, bytes]:
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

    def special_memory_size(self, ids: Optional[Set[int]] = None) -> SpecialTuple:
        return memory_utils.get_special_size(self.input_list, ids=ids)

    def _shrink_if_needed(self, end: int, ensure_byte_array: bool = False) -> None:
        if self.input_list:
            head_message = self.input_list[0]
            if end > len(head_message) or ensure_byte_array:
                if isinstance(head_message, bytearray):
                    head = self.input_list.popleft()
                else:
                    head = bytearray(self.input_list.popleft())
                while end > len(head) and self.input_list:
                    head.extend(self.input_list.popleft())  # pyre-ignore
                self.input_list.appendleft(head)
