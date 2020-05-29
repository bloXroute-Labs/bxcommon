from dataclasses import dataclass

from bxcommon.models.bdn_service_type import BdnServiceType
from bxcommon.models.time_interval_type import TimeIntervalType


@dataclass
class BdnServiceModelBase:
    interval: TimeIntervalType = TimeIntervalType.DAILY
    service_type: BdnServiceType = BdnServiceType.MSG_QUOTA
    expire_date: str = "1970-01-01 00:00:00"
    limit: int = 0