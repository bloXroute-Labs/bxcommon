from dataclasses import dataclass
from typing import Optional

from bxcommon.models.bdn_service_model_config_base import BdnServiceModelConfigBase


@dataclass
class BdnAccountModelBase:
    account_id: str
    logical_account_name: str
    certificate: str
    # TODO change expire_date to datetime type
    expire_date: str = "1970-01-01 00:00:00"
    tx_free: Optional[BdnServiceModelConfigBase] = None
    tx_paid: BdnServiceModelConfigBase = BdnServiceModelConfigBase()
    block_paid: BdnServiceModelConfigBase = BdnServiceModelConfigBase()
    cloud_api: BdnServiceModelConfigBase = BdnServiceModelConfigBase()
    new_transaction_streaming: BdnServiceModelConfigBase = BdnServiceModelConfigBase()
    blockchain_protocol: Optional[str] = None
    blockchain_network: Optional[str] = None
