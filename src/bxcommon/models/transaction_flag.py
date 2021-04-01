from bxcommon.models.quota_type_model import QuotaType
from bxcommon.models.serializable_flag import SerializableFlag


class TransactionFlag(SerializableFlag):
    NO_FLAGS = 0
    STATUS_MONITORING = 1
    PAID_TX = 2
    STATUS_TRACK = STATUS_MONITORING | PAID_TX
    NONCE_MONITORING = 4
    RE_PROPAGATE = 8
    NONCE_TRACK = NONCE_MONITORING | STATUS_TRACK

    # for professional/enterprise accounts only
    CEN_ENABLED = 16

    LOCAL_REGION = 32

    PRIVATE_TX = 64

    # adding more flags to avoid creating new converters
    TBD_2 = 128
    TBD_3 = 256
    TBD_4 = 512
    TBD_5 = 1024

    def get_quota_type(self) -> QuotaType:
        if TransactionFlag.PAID_TX in self:
            return QuotaType.PAID_DAILY_QUOTA
        else:
            return QuotaType.FREE_DAILY_QUOTA
