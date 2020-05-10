from enum import auto
from bxcommon.models.serializable_flag import SerializableFlag


class EntityType(SerializableFlag):
    TRANSACTION = auto()
    BLOCK = auto()

    def __str__(self):
        return str(self.name).lower()
