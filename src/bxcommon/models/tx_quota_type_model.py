from enum import auto
from bxcommon.models.serializable_flag import SerializableFlag


class TxQuotaType(SerializableFlag):
    FREE_DAILY_QUOTA = auto()
    PAID_DAILY_QUOTA = auto()

    def __str__(self):
        return self.name
