from typing import List, Optional

from bxcommon.messages.bloxroute.abstract_cleanup_message import AbstractCleanupMessage
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.utils import crypto
from bxcommon.utils.object_hash import Sha256Hash, NULL_SHA256_HASH


class TransactionCleanupMessage(AbstractCleanupMessage):
    MESSAGE_TYPE = BloxrouteMessageType.TRANSACTION_CLEANUP
    """
    Message with sids numbers for cleanup.
    """

    def __init__(self, network_num: Optional[int] = None, source_id: str = "", sids: Optional[List[int]] = None,
                 tx_hashes: Optional[List[Sha256Hash]] = None, buf: Optional[bytearray] = None):
        message_hash = NULL_SHA256_HASH
        build_buffer = buf is None

        super(TransactionCleanupMessage, self).__init__(message_hash, network_num, source_id, sids, tx_hashes, buf)
        if build_buffer:
            self.set_message_hash(
                Sha256Hash(crypto.double_sha256(self.buf[AbstractCleanupMessage.PAYLOAD_START_OFFSET:]))
            )

    def __repr__(self):
        return "TransactionCleanupMessage<message_hash: {}, network_num:{}, num_sids: {}, num_tx_hashes: {}>".format(
            self.message_hash(),
            self.network_num(),
            len(self.short_ids()),
            len(self.transaction_hashes())
        )
