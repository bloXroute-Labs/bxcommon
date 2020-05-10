from enum import Enum, auto


class ErrorCode(Enum):
    BLOCKED = auto()
    IGNORE_SEEN = auto()
    TIMED_OUT = auto()
    UNKNOWN_ERROR = auto()
