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

    ENTERPRISE_SENDER = 16
    LOCAL_REGION = 32
    PRIVATE_TX = 64
    ELITE_SENDER = 128
    DELIVER_TO_NODE = 256
    VALIDATORS_ONLY = 512

    # adding more flags to avoid creating new converters
    TBD_3 = 1024
    TBD_4 = 2048
    TBD_5 = 4096

    def get_quota_type(self) -> QuotaType:
        if TransactionFlag.PAID_TX in self:
            return QuotaType.PAID_DAILY_QUOTA
        else:
            return QuotaType.FREE_DAILY_QUOTA
