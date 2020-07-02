from typing import Optional
from dataclasses import dataclass
from datetime import datetime, date

from bxcommon.models.bdn_service_model_base import BdnServiceModelBase
from bxcommon import constants


@dataclass
class BdnServiceModelConfigBase:
    msg_quota: Optional[BdnServiceModelBase] = None
    permit: Optional[BdnServiceModelBase] = None
    expire_date: str = constants.EPOCH_DATE

    def is_service_valid(self) -> bool:
        today = datetime.utcnow().date()
        try:
            service_expire_date = date.fromisoformat(self.expire_date)
        except (KeyError, ValueError):
            return False

        return service_expire_date >= today
