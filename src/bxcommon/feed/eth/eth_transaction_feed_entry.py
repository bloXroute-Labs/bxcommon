from typing import Dict, Any, Union

from bxcommon.utils.blockchain_utils.eth import transaction_validation_utils
from bxcommon.utils.object_hash import Sha256Hash
from bxcommon import log_messages
from bxcommon.messages.eth.serializers.transaction import Transaction
from bxutils import logging

import blxr_rlp as rlp

logger = logging.get_logger(__name__)


class EthTransactionFeedEntry:
    tx_hash: str
    tx_contents: Dict[str, Any]
    local_region: bool

    def __init__(
        self, tx_hash: Sha256Hash,
        tx_contents: Union[memoryview, Dict[str, Any]],
        local_region: bool,
    ) -> None:
        self.tx_hash = f"0x{str(tx_hash)}"

        try:
            if isinstance(tx_contents, memoryview):
                transaction = transaction_validation_utils.parse_transaction(tx_contents)
                if transaction is None:
                    raise Exception("could not parse transaction from bytes")
                self.tx_contents = transaction.to_json()
            else:
                # normalize json from source
                self.tx_contents = Transaction.from_json(tx_contents).to_json()
        except Exception as e:
            tx_contents_str = tx_contents
            if isinstance(tx_contents, memoryview):
                tx_contents_str = tx_contents.tobytes()
            logger.error(
                log_messages.COULD_NOT_DESERIALIZE_TRANSACTION,
                tx_hash,
                tx_contents_str,
                e
            )
            raise e

        self.local_region = local_region

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, EthTransactionFeedEntry)
            and other.tx_hash == self.tx_hash
            and other.tx_contents == self.tx_contents
            and other.local_region == self.local_region
        )
