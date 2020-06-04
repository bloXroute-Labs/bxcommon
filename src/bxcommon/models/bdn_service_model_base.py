from dataclasses import dataclass
from datetime import datetime

from bxcommon.models.bdn_service_type import BdnServiceType
from bxcommon.models.time_interval_type import TimeIntervalType


@dataclass
class BdnServiceModelBase:
    interval: TimeIntervalType = TimeIntervalType.DAILY
    service_type: BdnServiceType = BdnServiceType.MSG_QUOTA
    expire_date: str = "1970-01-01 00:00:00"
    limit: int = 0

    def is_service_valid(self) -> bool:
        service_expire_date = datetime.fromisoformat(self.expire_date).date()
        today = datetime.utcnow().date()
        return today >= service_expire_date
