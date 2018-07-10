import struct

from bxcommon.constants import HDR_COMMON_OFF
from bxcommon.messages.message import Message
from bxcommon.utils.object_hash import ObjectHash


# Assign a transaction an id
class TxAssignMessage(Message):
    def __init__(self, tx_hash=None, short_id=None, buf=None):
        if buf is None:
            # 32 for tx_hash, 4 for short_id
            buf = bytearray(HDR_COMMON_OFF + 36)
            off = HDR_COMMON_OFF
            buf[off:off + 32] = tx_hash.binary
            off += 32
            struct.pack_into('<L', buf, off, short_id)
            off += 4

            Message.__init__(self, 'txassign', off - HDR_COMMON_OFF, buf)
        else:
            assert not isinstance(buf, str)
            self.buf = buf
            self._memoryview = memoryview(self.buf)
            self._tx_hash = self._short_id = None

    def tx_hash(self):
        if self._tx_hash is None:
            off = HDR_COMMON_OFF
            self._tx_hash = ObjectHash(self.buf[off:off + 32])
        return self._tx_hash

    def short_id(self):
        if self._short_id is None:
            self._short_id, = struct.unpack_from('<L', self.buf, HDR_COMMON_OFF + 32)
        return self._short_id
