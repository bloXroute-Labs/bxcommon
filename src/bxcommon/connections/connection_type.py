from enum import auto

from bxcommon.models.serializable_flag import SerializableFlag


# IntFlag allows comparison with ints, which is not as strict as Flag, but allows easier unit testing.
class ConnectionType(SerializableFlag):
    NONE = 0
    SDN = auto()
    BLOCKCHAIN_NODE = auto()
    REMOTE_BLOCKCHAIN_NODE = auto()
    EXTERNAL_GATEWAY = auto()
    RELAY_TRANSACTION = auto()
    RELAY_BLOCK = auto()
    RELAY_ALL = RELAY_TRANSACTION | RELAY_BLOCK
    CROSS_RELAY = auto()
    INTERNAL_GATEWAY = auto()
    GATEWAY = INTERNAL_GATEWAY | EXTERNAL_GATEWAY

    def __str__(self):
        return self.name

    def __format__(self, format_spec):
        return self.name
