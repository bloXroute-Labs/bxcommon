from typing import List, Optional

from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.abstract_cleanup_message import AbstractCleanupMessage
from bxcommon.utils.object_hash import Sha256Hash


class BlockConfirmationMessage(AbstractCleanupMessage):
    MESSAGE_TYPE = BloxrouteMessageType.BLOCK_CONFIRMATION
    """
    Message with sids numbers for cleanup.
    """

    def __init__(self, message_hash: Optional[Sha256Hash] = None, network_num: Optional[int] = None,
                 source_id: str = "", sids: Optional[List[int]] = None, tx_hashes: Optional[List[Sha256Hash]] = None,
                 buf: Optional[bytearray] = None):

        super(BlockConfirmationMessage, self).__init__(message_hash, network_num, source_id, sids, tx_hashes, buf)

    def block_hash(self) -> Sha256Hash:
        return self.message_hash()

    def __repr__(self):
        return "BlockConfirmationMessage <block_hash: {} :{}> <num_sids: {}> <num_tx_hashes: {}>".format(
            self.block_hash(),
            self._network_num,
            self._sids_count,
            self._tx_hashes_count
        )
