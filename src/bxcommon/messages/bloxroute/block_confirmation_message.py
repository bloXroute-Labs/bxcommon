from bxcommon.messages.bloxroute.abstract_cleanup_message import AbstractCleanupMessage
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.utils.object_hash import Sha256Hash


class BlockConfirmationMessage(AbstractCleanupMessage):
    MESSAGE_TYPE = BloxrouteMessageType.BLOCK_CONFIRMATION
    """
    Message with short ids for cleanup for cleanup.
    """

    def block_hash(self) -> Sha256Hash:
        return self.message_hash()

    def __repr__(self):
        return "BlockConfirmationMessage <block_hash: {} :{}> <num_sids: {}> <num_tx_hashes: {}>".format(
            self.block_hash(),
            self.network_num(),
            len(self.short_ids()),
            len(self.transaction_hashes())
        )
