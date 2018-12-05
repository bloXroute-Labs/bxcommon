# An enum that stores the different log levels
from enum import IntEnum


class LogLevel(IntEnum):
    DEBUG = 0
    INFO = 10
    STATS = 15
    WARN = 20
    ERROR = 30
    FATAL = 40

    def __str__(self):
        return self.name
