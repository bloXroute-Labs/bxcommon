from enum import Enum


class SerializableEnum(Enum):
    def __str__(self):
        return self.value
