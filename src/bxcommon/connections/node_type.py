from bxcommon.models.serializeable_flag import SerializeableFlag


class NodeType(SerializeableFlag):
    GATEWAY = 1
    RELAY_TRANSACTION = 2
    RELAY_BLOCK = 4
    RELAY = RELAY_TRANSACTION | RELAY_BLOCK

    def __str__(self):
        return self.name
