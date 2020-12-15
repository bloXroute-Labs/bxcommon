from typing import NamedTuple

from bxcommon import constants
from bxcommon.feed.feed import Feed
from bxcommon.models.tx_blockchain_status import TxBlockchainStatus
from bxcommon.utils.object_hash import Sha256Hash


class TransactionStatusFeedEntry:
    tx_hash: str
    status: str
    account_id: str

    def __init__(
        self,
        tx_hash: Sha256Hash,
        status: TxBlockchainStatus,
        account_id: str
    ) -> None:
        self.tx_hash = str(tx_hash)
        self.status = str(status)
        self.account_id = account_id

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, TransactionStatusFeedEntry)
            and other.tx_hash == self.tx_hash
            and other.status == self.status
            and other.account_id == self.account_id
        )


class TransactionStatus(NamedTuple):
    tx_hash: Sha256Hash
    status: TxBlockchainStatus
    account_id: str


class TransactionStatusFeed(Feed[TransactionStatusFeedEntry, TransactionStatus]):
    NAME = "transactionStatus"
    FIELDS = ["tx_hash", "status", "account_id"]
    ALL_FIELDS = FIELDS

    def __init__(self, network_num: int = constants.ALL_NETWORK_NUM) -> None:
        super().__init__(self.NAME, network_num)

    def serialize(self, raw_message: TransactionStatus) -> TransactionStatusFeedEntry:
        return TransactionStatusFeedEntry(raw_message.tx_hash, raw_message.status, raw_message.account_id)
