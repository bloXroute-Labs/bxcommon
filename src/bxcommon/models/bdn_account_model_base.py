from dataclasses import dataclass
from datetime import datetime, date
from enum import Enum
from functools import total_ordering
from typing import Optional

from bxcommon import constants
from bxcommon.models.bdn_service_model_config_base import (
    BdnBasicServiceModel,
    BdnQuotaServiceModelConfigBase,
    BdnFeedServiceModelConfigBase, BdnPrivateRelayServiceModelConfigBase,
    BdnLightGatewayServiceModelConfigBase)
from bxcommon.rpc import rpc_constants
from bxutils import logging

logger = logging.get_logger(__name__)
OPTIONAL_ACCOUNT_SERVICES = {"tx_free"}


@total_ordering
class Tiers(Enum):
    INTRODUCTORY = "Introductory"
    DEVELOPER = "Developer"
    PROFESSIONAL = "Professional"
    ENTERPRISE = "Enterprise"
    ENTERPRISE_ELITE = "EnterpriseElite"
    ULTRA = "Ultra"

    def __eq__(self, other):
        if not isinstance(other, Tiers):
            return NotImplemented

        # pylint: disable=comparison-with-callable
        return self.value == other.value

    def __hash__(self):
        return id(self)

    def __lt__(self, other):
        if not isinstance(other, Tiers):
            return NotImplemented

        order = [
            Tiers.INTRODUCTORY,
            Tiers.DEVELOPER,
            Tiers.PROFESSIONAL,
            Tiers.ENTERPRISE,
            Tiers.ENTERPRISE_ELITE,
            Tiers.ULTRA
        ]

        return order.index(self) < order.index(other)

    def __gt__(self, other):
        return not self.__lt__(other)

    def __ge__(self, other):
        return self.__gt__(other) or self.__eq__(other)

    @classmethod
    def from_string(cls, value: str) -> Optional["Tiers"]:
        try:
            return Tiers(value)
        except ValueError:
            return None

    def tier_article_prefix(self) -> str:
        if self in {Tiers.INTRODUCTORY, Tiers.ENTERPRISE, Tiers.ENTERPRISE_ELITE}:
            return "an"
        return "a"


@dataclass
class AccountInfo:
    account_id: str
    logical_account_name: str
    certificate: str
    # TODO change expire_date to datetime type
    expire_date: str = constants.EPOCH_DATE
    blockchain_protocol: Optional[str] = None
    blockchain_network: Optional[str] = None
    tier_name: Optional[str] = None
    is_miner: Optional[bool] = None
    mev_builder: Optional[str] = None
    mev_miner: Optional[str] = None
    metamask_rpc_to_flashbots: Optional[bool] = False


@dataclass
class AccountTemplate:
    # All items except tx_free are required.
    # Service Model is enabled/disabled according to the service expiry date, default disabled
    tx_free: Optional[BdnQuotaServiceModelConfigBase] = None
    tx_paid: Optional[BdnQuotaServiceModelConfigBase] = None
    block_paid: Optional[BdnQuotaServiceModelConfigBase] = None
    cloud_api: Optional[BdnBasicServiceModel] = None
    new_transaction_streaming: Optional[BdnFeedServiceModelConfigBase] = None
    new_block_streaming: Optional[BdnFeedServiceModelConfigBase] = None
    new_pending_transaction_streaming: Optional[BdnFeedServiceModelConfigBase] = None
    transaction_state_feed: Optional[BdnFeedServiceModelConfigBase] = None
    on_block_feed: Optional[BdnFeedServiceModelConfigBase] = None
    transaction_receipts_feed: Optional[BdnFeedServiceModelConfigBase] = None
    private_relays: Optional[BdnPrivateRelayServiceModelConfigBase] = None
    private_transaction: Optional[BdnQuotaServiceModelConfigBase] = None
    private_transaction_fee: Optional[BdnQuotaServiceModelConfigBase] = None
    light_gateway: Optional[BdnLightGatewayServiceModelConfigBase] = None
    online_gateways: Optional[BdnQuotaServiceModelConfigBase] = None
    tx_trace_rate_limitation: Optional[BdnQuotaServiceModelConfigBase] = None
    unpaid_tx_burst_limit: Optional[BdnQuotaServiceModelConfigBase] = None
    paid_tx_burst_limit: Optional[BdnQuotaServiceModelConfigBase] = None
    backbone_region_limit: Optional[BdnQuotaServiceModelConfigBase] = None
    region_limit: Optional[BdnQuotaServiceModelConfigBase] = None
    relay_limit: Optional[BdnQuotaServiceModelConfigBase] = None
    min_allowed_nodes: Optional[BdnQuotaServiceModelConfigBase] = None
    max_allowed_nodes: Optional[BdnQuotaServiceModelConfigBase] = None
    boost_mevsearcher: Optional[BdnBasicServiceModel] = None

@dataclass
class BdnAccountModelBase(AccountTemplate, AccountInfo):

    def is_account_valid(self) -> bool:
        today = datetime.utcnow().date()
        try:
            expire_date = date.fromisoformat(self.expire_date)
        except (KeyError, ValueError):
            return False

        return expire_date >= today

    # pylint: disable=too-many-return-statements
    def get_feed_service_config_by_name(
        self, feed_name: str
    ) -> Optional[BdnFeedServiceModelConfigBase]:
        if feed_name in {rpc_constants.NEW_TRANSACTION_FEED_NAME}:
            return self.new_transaction_streaming
        elif feed_name in {rpc_constants.ETH_PENDING_TRANSACTION_FEED_NAME}:
            return self.new_pending_transaction_streaming
        elif feed_name in {rpc_constants.NEW_BLOCKS_FEED_NAME}:
            return self.new_block_streaming
        elif feed_name in {rpc_constants.TRANSACTION_STATUS_FEED_NAME}:
            return self.transaction_state_feed
        elif feed_name in {rpc_constants.ETH_ON_BLOCK_FEED_NAME}:
            return self.on_block_feed
        elif feed_name in {rpc_constants.ETH_TRANSACTION_RECEIPTS_FEED_NAME}:
            return self.transaction_receipts_feed
        else:
            return None
