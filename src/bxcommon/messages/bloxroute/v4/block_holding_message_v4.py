import struct

from bxcommon import constants
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.v4.block_hash_message_v4 import BlockHashMessageV4
from bxcommon.utils import crypto
from bxcommon.utils.object_hash import ConcatHash


class BlockHoldingMessageV4(BlockHashMessageV4):
    """
    Request for other gateways to hold onto the block for a timeout to avoid encrypted block duplication.
    """
    MESSAGE_TYPE = BloxrouteMessageType.BLOCK_HOLDING
    PAYLOAD_LENGTH = crypto.SHA256_HASH_LEN + constants.NETWORK_NUM_LEN

    def __init__(self, block_hash=None, network_num=None, buf=None):
        if buf is None:
            buf = bytearray(constants.BX_HDR_COMMON_OFF + self.PAYLOAD_LENGTH)

            off = constants.BX_HDR_COMMON_OFF
            buf[off:off + crypto.SHA256_HASH_LEN] = block_hash.binary
            off += crypto.SHA256_HASH_LEN

            struct.pack_into("<L", buf, off, network_num)
            off += constants.NETWORK_NUM_LEN

        self.buf = buf
        self._block_hash = None
        self._block_id = None
        self._network_num = None
        super(BlockHashMessageV4, self).__init__(self.MESSAGE_TYPE, self.PAYLOAD_LENGTH, buf)

    def network_num(self):
        if self._network_num is None:
            off = constants.BX_HDR_COMMON_OFF + crypto.SHA256_HASH_LEN
            self._network_num, = struct.unpack_from("<L", self._memoryview, off)
        return self._network_num

    def block_id(self):
        if self._block_id is None:
            off = constants.BX_HDR_COMMON_OFF
            # Hash over the SHA256 hash and the network number.
            self._block_id = ConcatHash(self._memoryview[off:off + crypto.SHA256_HASH_LEN + constants.NETWORK_NUM_LEN],
                                        0)
        return self._block_id

    def __repr__(self):
        return "BlockHoldingMessage<block_hash: {}>".format(self.block_hash())
