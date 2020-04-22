from enum import Enum


class LogFormat(Enum):
    JSON = "JSON"
    PLAIN = "PLAIN"

    def __str__(self):
        return self.name
