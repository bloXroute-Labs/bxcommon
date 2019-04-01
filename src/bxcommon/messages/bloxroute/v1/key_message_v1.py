from bxcommon.constants import HDR_COMMON_OFF
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.message import Message
from bxcommon.utils.crypto import KEY_SIZE, SHA256_HASH_LEN
from bxcommon.utils.object_hash import Sha256Hash


class KeyMessageV1(Message):
    MESSAGE_TYPE = BloxrouteMessageType.KEY

    def __init__(self, msg_hash=None, key=None, buf=None):
        if buf is None:
            assert len(key) == KEY_SIZE
            self.buf = bytearray(HDR_COMMON_OFF + SHA256_HASH_LEN + KEY_SIZE)

            off = HDR_COMMON_OFF
            self.buf[off:off + SHA256_HASH_LEN] = msg_hash.binary
            off += SHA256_HASH_LEN
            self.buf[off:off + KEY_SIZE] = key
            off += KEY_SIZE

            super(KeyMessageV1, self).__init__(self.MESSAGE_TYPE, off - HDR_COMMON_OFF, self.buf)
        else:
            assert not isinstance(buf, str)
            self.buf = buf
            self._memoryview = memoryview(self.buf)

        self._key = None
        self._block_hash = None

    def block_hash(self):
        if self._block_hash is None:
            self._block_hash = Sha256Hash(self._memoryview[HDR_COMMON_OFF:HDR_COMMON_OFF + SHA256_HASH_LEN])
        return self._block_hash

    def key(self):
        if self._key is None:
            off = HDR_COMMON_OFF + SHA256_HASH_LEN
            self._key = self._memoryview[off:off + self.payload_len()]
        return self._key
