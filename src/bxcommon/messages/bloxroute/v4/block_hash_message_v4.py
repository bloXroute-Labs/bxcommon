from abc import ABCMeta

from bxcommon import constants
from bxcommon.messages.bloxroute.v4.message_v4 import MessageV4
from bxcommon.utils import crypto
from bxcommon.utils.object_hash import Sha256Hash


class BlockHashMessageV4(MessageV4):
    __metaclass__ = ABCMeta

    MESSAGE_TYPE = b""
    PAYLOAD_LENGTH = crypto.SHA256_HASH_LEN

    def __init__(self, block_hash=None, buf=None):
        if buf is None:
            buf = bytearray(constants.BX_HDR_COMMON_OFF + self.PAYLOAD_LENGTH)

            off = constants.BX_HDR_COMMON_OFF
            buf[off:off + crypto.SHA256_HASH_LEN] = block_hash.binary
            off += crypto.SHA256_HASH_LEN

        self.buf = buf
        self._block_hash = None
        super(BlockHashMessageV4, self).__init__(self.MESSAGE_TYPE, self.PAYLOAD_LENGTH, buf)

    def block_hash(self):
        if self._block_hash is None:
            off = constants.BX_HDR_COMMON_OFF
            self._block_hash = Sha256Hash(self._memoryview[off:off + crypto.SHA256_HASH_LEN])
        return self._block_hash
