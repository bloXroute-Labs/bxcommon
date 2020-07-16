from abc import ABC
from typing import Optional

from bxcommon import constants
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.utils import crypto
from bxcommon.utils.object_hash import Sha256Hash


class BlockHashMessage(AbstractBloxrouteMessage, ABC):
    PAYLOAD_LENGTH = crypto.SHA256_HASH_LEN + constants.CONTROL_FLAGS_LEN

    def __init__(self, block_hash=None, buf=None) -> None:
        if buf is None:
            buf = bytearray(self.HEADER_LENGTH + self.PAYLOAD_LENGTH)

            off = self.HEADER_LENGTH
            buf[off:off + crypto.SHA256_HASH_LEN] = block_hash.binary
            off += crypto.SHA256_HASH_LEN

        self.buf = buf
        self._block_hash: Optional[Sha256Hash] = None
        super(BlockHashMessage, self).__init__(self.MESSAGE_TYPE, self.PAYLOAD_LENGTH, buf)

    def block_hash(self) -> Sha256Hash:
        block_hash = self._block_hash
        if block_hash is None:
            off = self.HEADER_LENGTH
            block_hash = Sha256Hash(self._memoryview[off:off + crypto.SHA256_HASH_LEN])
            self._block_hash = block_hash
        return block_hash
