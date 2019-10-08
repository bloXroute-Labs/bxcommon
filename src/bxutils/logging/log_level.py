import logging
from enum import IntEnum


class LogLevel(IntEnum):
    CRITICAL = 50
    FATAL = CRITICAL
    ERROR = 40
    WARNING = 30
    WARN = WARNING
    STATS = 25
    INFO = 20
    DEBUG = 10
    TRACE = 5
    NOTSET = 0


logging.addLevelName(LogLevel.STATS, "STATS")
logging.addLevelName(LogLevel.TRACE, "TRACE")


def from_string(level: str) -> LogLevel:
    return LogLevel[level.upper()]
