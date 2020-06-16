from bxcommon.models.serializable_flag import SerializableFlag


class EntityType(SerializableFlag):
    TRANSACTION = 1
    BLOCK = 2

    def __str__(self):
        return str(self.name).lower()
