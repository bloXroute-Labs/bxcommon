import struct

from bxutils.logging.log_level import LogLevel

from bxcommon.constants import BX_HDR_COMMON_OFF, NETWORK_NUM_LEN
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.v4.message_v4 import MessageV4
from bxcommon.utils.crypto import KEY_SIZE, SHA256_HASH_LEN
from bxcommon.utils.object_hash import Sha256Hash, ConcatHash


class KeyMessageV4(MessageV4):
    MESSAGE_TYPE = BloxrouteMessageType.KEY

    def __init__(self, msg_hash=None, network_num=None, key=None, buf=None):
        if buf is None:
            assert len(key) == KEY_SIZE
            self.buf = bytearray(BX_HDR_COMMON_OFF + SHA256_HASH_LEN + KEY_SIZE + NETWORK_NUM_LEN)

            off = BX_HDR_COMMON_OFF
            self.buf[off:off + SHA256_HASH_LEN] = msg_hash.binary
            off += SHA256_HASH_LEN
            struct.pack_into("<L", self.buf, off, network_num)
            off += NETWORK_NUM_LEN
            self.buf[off:off + KEY_SIZE] = key
            off += KEY_SIZE

            super(KeyMessageV4, self).__init__(self.MESSAGE_TYPE, off - BX_HDR_COMMON_OFF, self.buf)
        else:
            assert not isinstance(buf, str)
            self.buf = buf
            self._memoryview = memoryview(self.buf)

        self._key = None
        self._block_id = None
        self._network_num = None
        self._block_hash = None
        self._payload_len = None
        self._payload = None

    def log_level(self):
        return LogLevel.INFO

    def block_hash(self):
        """
        The hash of the data block that is being returned.
        """
        if self._block_hash is None:
            off = BX_HDR_COMMON_OFF
            self._block_hash = Sha256Hash(self._memoryview[off:off + SHA256_HASH_LEN])
        return self._block_hash

    def block_id(self):
        if self._block_id is None:
            off = BX_HDR_COMMON_OFF
            # Hash over the SHA256 hash and the network number.
            self._block_id = ConcatHash(self._memoryview[off:off + SHA256_HASH_LEN + NETWORK_NUM_LEN], 0)
        return self._block_id

    def network_num(self):
        if self._network_num is None:
            off = BX_HDR_COMMON_OFF + SHA256_HASH_LEN
            self._network_num, = struct.unpack_from("<L", self.buf, off)

        return self._network_num

    def key(self):
        if self._key is None:
            off = BX_HDR_COMMON_OFF + SHA256_HASH_LEN + NETWORK_NUM_LEN
            self._key = self._memoryview[off:off + KEY_SIZE]
        return self._key

    def __repr__(self):
        return "KeyMessage<network_num: {}, block_id: {}".format(self.network_num(),
                                                                 self.block_id())
