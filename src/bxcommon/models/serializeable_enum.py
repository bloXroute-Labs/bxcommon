from enum import Enum


class SerializeableEnum(Enum):

    def __hash__(self):
        return hash(self.value)

    def __str__(self) -> str:
        return str(self.value)
