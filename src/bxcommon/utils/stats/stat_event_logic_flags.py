from enum import Flag


class StatEventLogicFlags(Flag):
    NONE = 0
    BLOCK_INFO = 1
    MATCH = 2
    SUMMARY = 4
    PROPAGATION_START = 8
    PROPAGATION_END = 16

    def __str__(self) -> str:
        return str(self.value)
