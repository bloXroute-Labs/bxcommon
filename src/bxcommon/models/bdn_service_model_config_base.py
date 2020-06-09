from typing import Optional
from dataclasses import dataclass
from datetime import datetime, date

from bxutils import constants as utils_constants
from bxcommon.models.bdn_service_model_base import BdnServiceModelBase


@dataclass
class BdnServiceModelConfigBase:
    msg_quota: Optional[BdnServiceModelBase] = None
    permit: Optional[BdnServiceModelBase] = None
    expire_date: str = utils_constants.DEFAULT_EXPIRATION_DATE.isoformat()

    def is_service_valid(self) -> bool:
        today = datetime.utcnow().date()
        try:
            service_expire_date = date.fromisoformat(self.expire_date)
        except (KeyError, ValueError):
            return False

        return service_expire_date >= today
