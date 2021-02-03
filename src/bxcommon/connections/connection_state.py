from enum import auto

from bxcommon.models.serializable_flag import SerializableFlag


class ConnectionState(SerializableFlag):
    CONNECTING = auto()
    INITIALIZED = auto()
    HELLO_RECVD = auto()
    HELLO_ACKD = auto()

    # avoid all future usages of ConnectionState.ESTABLISHED
    ESTABLISHED = auto()

    CUT_THROUGH_SOURCE = auto()
    CUT_THROUGH_SINK = auto()
    ULTRA_SLOW = auto()

    def __str__(self) -> str:
        # pylint: disable=using-constant-test
        if self.name:
            return str(self.name)
        else:
            return super().__str__()
