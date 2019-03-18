import struct

from bxcommon import constants
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.utils import crypto
from bxcommon.messages.bloxroute.block_hash_message import BlockHashMessage


class BlockHoldingMessage(BlockHashMessage):
    """
    Request for other gateways to hold onto the block for a timeout to avoid encrypted block duplication.
    """
    MESSAGE_TYPE = BloxrouteMessageType.BLOCK_HOLDING
    PAYLOAD_LENGTH = crypto.SHA256_HASH_LEN + constants.NETWORK_NUM_LEN

    def __init__(self, block_hash=None, network_num=None, buf=None):
        if buf is None:
            buf = bytearray(constants.HDR_COMMON_OFF + self.PAYLOAD_LENGTH)

            off = constants.HDR_COMMON_OFF
            buf[off:off + crypto.SHA256_HASH_LEN] = block_hash.binary
            off += crypto.SHA256_HASH_LEN

            struct.pack_into("<L", buf, off, network_num)
            off += constants.NETWORK_NUM_LEN

        self.buf = buf
        self._block_hash = None
        self._network_num = None
        super(BlockHashMessage, self).__init__(self.MESSAGE_TYPE, self.PAYLOAD_LENGTH, buf)

    def network_num(self):
        if self._network_num is None:
            off = constants.HDR_COMMON_OFF + crypto.SHA256_HASH_LEN
            self._network_num, = struct.unpack_from("<L", self._memoryview, off)
        return self._network_num

    def __repr__(self):
        return "BlockHoldingMessage<block_hash: {}>".format(self.block_hash())
