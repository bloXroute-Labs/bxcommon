from typing import NamedTuple

from bxcommon.feed.feed import Feed
from bxcommon.models.tx_blockchain_status import TxBlockchainStatus
from bxcommon.utils.object_hash import Sha256Hash


class TransactionStatusFeedEntry:
    tx_hash: str
    status: str

    def __init__(
        self,
        tx_hash: Sha256Hash,
        status: TxBlockchainStatus
    ) -> None:
        self.tx_hash = str(tx_hash)
        self.status = str(status)

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, TransactionStatusFeedEntry)
            and other.tx_hash == self.tx_hash
            and other.status == self.status
        )


class TransactionStatus(NamedTuple):
    tx_hash: Sha256Hash
    status: TxBlockchainStatus


class TransactionStatusFeed(Feed[TransactionStatusFeedEntry, TransactionStatus]):
    NAME = "transactionStatus"
    FIELDS = ["tx_hash", "status"]

    def __init__(self) -> None:
        super().__init__(self.NAME)

    def serialize(self, raw_message: TransactionStatus) -> TransactionStatusFeedEntry:
        return TransactionStatusFeedEntry(raw_message.tx_hash, raw_message.status)
