from typing import Dict, Any

from bxcommon import constants
from bxcommon.rpc.rpc_errors import RpcInvalidParams
from bxcommon.rpc import rpc_constants
from bxcommon.feed.feed import Feed
from bxcommon.feed.subscriber import Subscriber
from bxcommon.utils.alarm_queue import AlarmQueue
from bxcommon.utils.expiring_set import ExpiringSet
from bxcommon.utils.object_hash import Sha256Hash
from bxcommon.feed.eth.eth_transaction_feed_entry import EthTransactionFeedEntry
from bxcommon.feed.eth.eth_raw_transaction import EthRawTransaction
from bxcommon.feed.eth import eth_filter_handlers
from bxutils import logging
from bxutils.logging.log_record_type import LogRecordType

logger = logging.get_logger()
logger_filters = logging.get_logger(LogRecordType.TransactionFiltering, __name__)

EXPIRATION_TIME_S = 5 * 60


class EthPendingTransactionFeed(Feed[EthTransactionFeedEntry, EthRawTransaction]):
    NAME = rpc_constants.ETH_PENDING_TRANSACTION_FEED_NAME
    FIELDS = [
        "tx_hash",
        "tx_contents",
        "tx_contents.nonce",
        "tx_contents.gas_price",
        "tx_contents.gas",
        "tx_contents.to",
        "tx_contents.value",
        "tx_contents.input",
        "tx_contents.v",
        "tx_contents.r",
        "tx_contents.s",
        "tx_contents.from",
        "local_region",
    ]
    FILTERS = {"value", "from", "to", "gas_price", "method_id"}
    ALL_FIELDS = ["tx_hash", "tx_contents", "local_region"]

    published_transactions: ExpiringSet[Sha256Hash]

    def __init__(self, alarm_queue: AlarmQueue, network_num: int = constants.ALL_NETWORK_NUM,) -> None:
        super().__init__(self.NAME, network_num=network_num)

        # enforce uniqueness, since multiple sources can publish to
        # pending transactions (eth ws + remote)
        self.published_transactions = ExpiringSet(
            alarm_queue, EXPIRATION_TIME_S, "pendingTxs"
        )

    def subscribe(self, options: Dict[str, Any]) -> Subscriber[EthTransactionFeedEntry]:
        duplicates = options.get("duplicates", None)
        if duplicates is not None:
            if not isinstance(duplicates, bool):
                raise RpcInvalidParams('"duplicates" must be a boolean')

        return super().subscribe(options)

    def publish(self, raw_message: EthRawTransaction) -> None:
        if (
            raw_message.tx_hash in self.published_transactions
            and not self.any_subscribers_want_duplicates()
        ):
            return

        super().publish(raw_message)

        self.published_transactions.add(raw_message.tx_hash)

    def serialize(self, raw_message: EthRawTransaction) -> EthTransactionFeedEntry:
        return EthTransactionFeedEntry(
            raw_message.tx_hash,
            raw_message.tx_contents,
            raw_message.local_region
        )

    def any_subscribers_want_duplicates(self) -> bool:
        for subscriber in self.subscribers.values():
            if subscriber.options.get("duplicates", False):
                return True
        return False

    def should_publish_message_to_subscriber(
        self,
        subscriber: Subscriber[EthTransactionFeedEntry],
        raw_message: EthRawTransaction,
        serialized_message: EthTransactionFeedEntry,
    ) -> bool:
        if (
            raw_message.tx_hash in self.published_transactions
            and not subscriber.options.get("duplicates", False)
        ):
            return False
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
