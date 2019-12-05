from enum import auto
from bxcommon.models.serializable_flag import SerializableFlag


class TxQuotaType(SerializableFlag):
    FREE_DAILY_QUOTA = auto()
    PAID_DAILY_QUOTA = auto()

    def __str__(self):
        return self.name


def from_string(quota_type: str) -> TxQuotaType:
    return TxQuotaType[quota_type.upper()]
