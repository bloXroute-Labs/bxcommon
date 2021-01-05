from typing import Optional, Dict
from dataclasses import dataclass
from datetime import datetime, date

from bxcommon.models.bdn_service_model_base import BdnServiceModelBase, FeedServiceModelBase
from bxcommon import constants


@dataclass
class BdnBasicServiceModel:
    expire_date: str = constants.EPOCH_DATE

    def is_service_valid(self) -> bool:
        today = datetime.utcnow().date()
        try:
            service_expire_date = date.fromisoformat(self.expire_date)
        except (KeyError, ValueError):
            return False

        return service_expire_date >= today


@dataclass
class BdnServiceModelConfigBase(BdnBasicServiceModel):
    msg_quota: Optional[BdnServiceModelBase] = None
    permit: Optional[BdnServiceModelBase] = None
    feed: Optional[FeedServiceModelBase] = None


@dataclass
class BdnQuotaServiceModelConfigBase(BdnBasicServiceModel):
    msg_quota: Optional[BdnServiceModelBase] = None


@dataclass
class BdnFeedServiceModelConfigBase(BdnBasicServiceModel):
    feed: Optional[FeedServiceModelBase] = None


@dataclass
class BdnPrivateRelayServiceModelConfigBase(BdnBasicServiceModel):
    regions: Optional[Dict[str, str]] = None

    def is_region_valid(self, region: str) -> bool:
        if self.regions is not None:
            regions = self.regions
            assert regions is not None
            region_expire_date_str = regions.get(region, constants.EPOCH_DATE)
            try:
                region_expire_date = date.fromisoformat(region_expire_date_str)
            except (KeyError, ValueError):
                return False

            today = datetime.utcnow().date()
            return region_expire_date >= today
        return False
