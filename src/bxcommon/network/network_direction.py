from enum import Enum


class NetworkDirection(Enum):
    INBOUND = 1
    OUTBOUND = 2

    def __str__(self):
        return self.name
