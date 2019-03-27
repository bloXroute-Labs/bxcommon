# An enum that stores the different log levels
from enum import Enum


class LogFormat(Enum):
    JSON = "JSON"
    PLAIN = "PLAIN"

    def __str__(self):
        return self.name
