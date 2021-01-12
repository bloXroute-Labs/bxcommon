from typing import NamedTuple, Dict, Any

from bxcommon import constants
from bxcommon.rpc.rpc_errors import RpcInvalidParams
from bxcommon.utils import convert
from bxcommon.utils.object_hash import Sha256Hash
from bxcommon.rpc import rpc_constants
from bxcommon.feed.feed import Feed
from bxcommon.feed.subscriber import Subscriber
from bxcommon.feed.feed_source import FeedSource
from bxutils import logging

logger = logging.get_logger(__name__)


class RawTransactionFeedEntry:
    tx_hash: str
    tx_contents: str
    local_region: bool

    def __init__(
        self,
        tx_hash: Sha256Hash,
        tx_contents: memoryview,
        local_region: bool
    ) -> None:
        self.tx_hash = str(tx_hash)
        self.tx_contents = convert.bytes_to_hex(tx_contents)
        self.local_region = local_region

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, RawTransactionFeedEntry)
            and other.tx_hash == self.tx_hash
            and other.tx_contents == self.tx_contents
            and other.local_region == self.local_region
        )


class RawTransaction(NamedTuple):
    tx_hash: Sha256Hash
    tx_contents: memoryview
    source: FeedSource
    local_region: bool


class NewTransactionFeed(Feed[RawTransactionFeedEntry, RawTransaction]):
    NAME = rpc_constants.NEW_TRANSACTION_FEED_NAME
    FIELDS = ["tx_hash", "tx_contents", "local_region"]
    ALL_FIELDS = FIELDS

    def __init__(self, network_num: int = constants.ALL_NETWORK_NUM,) -> None:
        super().__init__(self.NAME, network_num)

    def subscribe(
        self, options: Dict[str, Any]
    ) -> Subscriber[RawTransactionFeedEntry]:
        include_from_blockchain = options.get("include_from_blockchain", None)
        if include_from_blockchain is not None:
            if not isinstance(include_from_blockchain, bool):
                raise RpcInvalidParams(
                    "\"include_from_blockchain\" must be a boolean"
                )
        return super().subscribe(options)

    def serialize(self, raw_message: RawTransaction) -> RawTransactionFeedEntry:
        return RawTransactionFeedEntry(
            raw_message.tx_hash, raw_message.tx_contents, raw_message.local_region
        )

    # pylint: disable=unused-argument
    def should_publish_message_to_subscriber(
        self,
        subscriber: Subscriber[RawTransactionFeedEntry],
        raw_message: RawTransaction,
        serialized_message: RawTransactionFeedEntry
    ) -> bool:
        if (
            raw_message.source == FeedSource.BLOCKCHAIN_SOCKET
            and not subscriber.options.get("include_from_blockchain", False)
        ):
            return False
        else:
            return True
