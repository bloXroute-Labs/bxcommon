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
    RELAY_PROXY = auto()

    def __str__(self):
        return str(self.name)

    def __format__(self, format_spec):
        return str(self.name)

    def format_short(self):
        cls = self.__class__
        if self in cls.RELAY_ALL:
            return "R"
        if self in cls.BLOCKCHAIN_NODE:
            return "B"
        if self in cls.REMOTE_BLOCKCHAIN_NODE:
            return "RemoteB"
        if self in cls.GATEWAY:
            return "G"

        return self.name
