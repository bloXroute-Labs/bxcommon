from enum import Enum


class SerializeableEnum(Enum):
    def __str__(self):
        return self.value
