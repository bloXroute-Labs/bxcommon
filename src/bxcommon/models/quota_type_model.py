from bxcommon.models.serializable_flag import SerializableFlag


class QuotaType(SerializableFlag):
    FREE_DAILY_QUOTA = 1
    PAID_DAILY_QUOTA = 2

    def __str__(self):
        return str(self.name).lower()[:4]
