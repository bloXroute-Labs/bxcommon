from typing import Optional
from dataclasses import dataclass
from datetime import datetime, date

from bxcommon.models.bdn_service_model_base import BdnServiceModelBase


@dataclass
class BdnServiceModelConfigBase:
    msg_quota: Optional[BdnServiceModelBase] = None
    permit: Optional[BdnServiceModelBase] = None
    expire_date: str = "1970-01-01"

    def is_service_valid(self) -> bool:
        today = datetime.utcnow().date()
        try:
            service_expire_date = date.fromisoformat(self.expire_date)
        except (KeyError, ValueError):
            return False

        return service_expire_date >= today
