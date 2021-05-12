from typing import Dict, Any, Union

from bxcommon.feed.eth.eth_transaction_feed_entry import EthTransactionFeedEntry
from bxcommon.utils.object_hash import Sha256Hash


class EthTransactionNoSignatureFeedEntry(EthTransactionFeedEntry):
    def __init__(self, tx_hash: Sha256Hash, tx_contents: Union[memoryview, Dict[str, Any]], local_region: bool):
        super().__init__(tx_hash, tx_contents, local_region)
        self.tx_contents.pop("v", None)
        self.tx_contents.pop("r", None)
        self.tx_contents.pop("s", None)
