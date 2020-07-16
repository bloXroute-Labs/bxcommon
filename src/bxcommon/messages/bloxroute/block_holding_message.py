from typing import Optional

from bxcommon.messages.bloxroute.abstract_broadcast_message import AbstractBroadcastMessage
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.utils.object_hash import Sha256Hash


class BlockHoldingMessage(AbstractBroadcastMessage):
    """
    Request for other gateways to hold onto the block for a timeout to avoid encrypted block duplication.
    """
    MESSAGE_TYPE = BloxrouteMessageType.BLOCK_HOLDING

    def __init__(self, block_hash: Optional[Sha256Hash] = None, network_num: Optional[int] = None,
                 source_id: str = "", buf: Optional[bytearray] = None):
        self._block_id = None
        super().__init__(block_hash, network_num, source_id, buf)

    def __repr__(self) -> str:
        return f"BlockHoldingMessage<block_hash: {self.block_hash()}>"

    def block_hash(self) -> Sha256Hash:
        return self.message_hash()
