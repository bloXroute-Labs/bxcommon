from enum import auto

from bxcommon.models.serializable_flag import SerializableFlag


class TxBlockchainStatus(SerializableFlag):
    UNKNOWN = auto()
    PROPAGATING = auto()
    REPROPAGATE = auto()
    TX_POOL = auto()
    MULTIPLE_TX_POOL = auto()
    MINED = auto()
    CONFIRMED = auto()
    DROPPED = auto()
    SPEEDUP = auto()
    CANCELED = auto()

    def __str__(self) -> str:
        # pylint: disable=using-constant-test
        if self.name:
            return str(self.name)
        else:
            return super().__str__()
