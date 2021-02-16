from typing import List, Set

from bxcommon import constants
from bxcommon.feed.eth import eth_filter_handlers
from bxcommon.feed.eth.eth_raw_transaction import EthRawTransaction
from bxcommon.feed.eth.eth_transaction_feed_entry import EthTransactionFeedEntry
from bxcommon.feed.feed import Feed
from bxcommon.feed.subscriber import Subscriber

from bxutils import logging
from bxutils.logging import LogRecordType

logger = logging.get_logger(__name__)
logger_filters = logging.get_logger(LogRecordType.TransactionFiltering, __name__)


class EthTransactionProxyFeed(Feed[EthTransactionFeedEntry, EthRawTransaction]):

    def __init__(
        self,
        name: str,
        fields: List[str],
        filters: Set[str],
        network_num: int = constants.ALL_NETWORK_NUM,
    ) -> None:
        # pylint: disable=invalid-name
        self.NAME = name
        self.FIELDS = fields
        self.FILTERS = filters

        super().__init__(self.NAME, network_num)

    def serialize(self, raw_message: EthRawTransaction) -> EthTransactionFeedEntry:
        return EthTransactionFeedEntry(
            raw_message.tx_hash,
            raw_message.tx_contents,
            raw_message.local_region
        )

    def should_publish_message_to_subscriber(
        self,
        subscriber: Subscriber[EthTransactionFeedEntry],
        # pylint: disable=unused-argument
        raw_message: EthRawTransaction,
        serialized_message: EthTransactionFeedEntry,
    ) -> bool:
        should_publish = True
        if subscriber.filters:
            logger_filters.trace(
                "checking if should publish to {} with filters {}",
                subscriber.subscription_id,
                subscriber.filters,
            )
            contents = serialized_message.tx_contents
            state = {
                "value": eth_filter_handlers.reformat_tx_value(contents["value"]),
                "to": eth_filter_handlers.reformat_address(contents["to"]),
                "from": eth_filter_handlers.reformat_address(contents["from"]),
                "gas_price": eth_filter_handlers.reformat_gas_price(contents["gas_price"]),
                "method_id": eth_filter_handlers.reformat_input_to_method_id(contents["input"]),
            }
            should_publish = subscriber.validate(state)
            logger_filters.trace("should publish: {}", should_publish)
        return should_publish
