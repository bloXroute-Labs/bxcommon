from enum import Enum


class SerializeableEnum(Enum):

    # From bxapi
    def __hash__(self):
        return hash(self.value)

    def __str__(self):
        return self.value
