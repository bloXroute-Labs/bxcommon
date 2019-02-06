# An enum that stores the different log levels
from enum import IntEnum


class LogLevel(IntEnum):
    DEBUG = 0
    TRACE = 5
    INFO = 10
    WARN = 20
    ERROR = 30
    FATAL = 40
    STATS = 50
    OFF = 100

    def __str__(self):
        return self.name
