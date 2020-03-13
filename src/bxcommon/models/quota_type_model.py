from enum import auto
from bxcommon.models.serializable_flag import SerializableFlag


class QuotaType(SerializableFlag):
    FREE_DAILY_QUOTA = auto()
    PAID_DAILY_QUOTA = auto()
