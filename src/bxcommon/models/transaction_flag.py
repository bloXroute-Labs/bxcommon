from bxcommon.models.quota_type_model import QuotaType
from bxcommon.models.serializable_flag import SerializableFlag


class TransactionFlag(SerializableFlag):
    NO_FLAGS = 0
    STATUS_TRACK = 1
    PAID_TX = 2
    NONCE = 4
    RE_PROPAGATE = 8
    PAID_STATUS_TRACK = STATUS_TRACK | PAID_TX

    def __str__(self):
        return str(self.name).lower()

    def get_quota_type(self) -> QuotaType:
        if TransactionFlag.PAID_TX in self:
            return QuotaType.PAID_DAILY_QUOTA
        else:
            return QuotaType.FREE_DAILY_QUOTA
