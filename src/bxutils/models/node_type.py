import enum
from bxutils.models.serializable_flag import SerializableFlag

# TODO : remove old reference in bxcommon and bxapi


class NodeType(SerializableFlag):
    INTERNAL_GATEWAY = enum.auto()
    EXTERNAL_GATEWAY = enum.auto()
    GATEWAY = INTERNAL_GATEWAY | EXTERNAL_GATEWAY
    RELAY_TRANSACTION = enum.auto()
    RELAY_BLOCK = enum.auto()
    RELAY = RELAY_TRANSACTION | RELAY_BLOCK
    API = enum.auto()
    API_SOCKET = enum.auto()

    def __str__(self):
        return self.name
