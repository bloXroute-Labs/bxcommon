from dataclasses import dataclass
from typing import Optional
from datetime import datetime, date

from bxcommon.models.bdn_service_model_config_base import (
    BdnBasicServiceModel,
    BdnQuotaServiceModelConfigBase,
    BdnFeedServiceModelConfigBase, BdnPrivateRelayServiceModelConfigBase,
)
from bxcommon import constants
from bxcommon.rpc import rpc_constants
from bxutils import logging

logger = logging.get_logger(__name__)
OPTIONAL_ACCOUNT_SERVICES = {"tx_free"}


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
