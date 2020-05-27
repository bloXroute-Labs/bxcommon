from typing import Optional
from dataclasses import dataclass

from bxcommon.models.bdn_service_model_base import BdnServiceModelBase


@dataclass
class BdnServiceModelConfigBase:
    msg_quota: Optional[BdnServiceModelBase] = None
    permit: Optional[BdnServiceModelBase] = None
