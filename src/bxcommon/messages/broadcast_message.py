import struct

from bxcommon.constants import HDR_COMMON_OFF, SHA256_HASH_LEN
from bxcommon.messages.message import Message
from bxcommon.utils.object_hash import ObjectHash


class BroadcastMessage(Message):
    def __init__(self, msg_hash=None, blob=None, buf=None):
        if buf is None:
            buf = bytearray(HDR_COMMON_OFF + SHA256_HASH_LEN + len(blob))
            self.buf = buf

            off = HDR_COMMON_OFF
            self.buf[off:off + SHA256_HASH_LEN] = msg_hash.binary
            off += SHA256_HASH_LEN
            self.buf[off:off + len(blob)] = blob
            off += len(blob)

            Message.__init__(self, 'broadcast', off - HDR_COMMON_OFF, buf)
        else:
            assert not isinstance(buf, str)
            self.buf = buf
            self._memoryview = memoryview(self.buf)

        self._blob = self._msg_hash = None

    def msg_hash(self):
        if self._msg_hash is None:
            off = HDR_COMMON_OFF
            self._msg_hash = ObjectHash(self._memoryview[off:off + SHA256_HASH_LEN])
        return self._msg_hash

    def blob(self):
        if self._blob is None:
            off = HDR_COMMON_OFF + SHA256_HASH_LEN
            self._blob = self._memoryview[off:off + self.payload_len()]

        return self._blob

    @staticmethod
    def peek_message(input_buffer):
        buf = input_buffer.peek_message(HDR_COMMON_OFF + SHA256_HASH_LEN)

        # FIXME statement does nothing, and returning false,none,none breaks tests
        # if len(buf) < HDR_COMMON_OFF + SHA256_HASH_LEN:
        #     False, None, None
        _, length = struct.unpack_from('<12sL', buf, 0)
        msg_hash = ObjectHash(buf[HDR_COMMON_OFF:HDR_COMMON_OFF + SHA256_HASH_LEN])
        return True, msg_hash, length
