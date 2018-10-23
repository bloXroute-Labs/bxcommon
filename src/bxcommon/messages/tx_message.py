import struct

from bxcommon import constants
from bxcommon.constants import HDR_COMMON_OFF, SHA256_HASH_LEN
from bxcommon.messages.message import Message
from bxcommon.utils.object_hash import ObjectHash

_SID_LEN = constants.UL_INT_SIZE_IN_BYTES
_NULL_SID = constants.NULL_TX_SID


class TxMessage(Message):
    def __init__(self, tx_hash=None, tx_val=None, buf=None, sid=_NULL_SID):
        self._tx_hash = None
        self._short_id = None
        self._tx_val = None

        if buf is None:
            buf = bytearray(HDR_COMMON_OFF + SHA256_HASH_LEN + _SID_LEN)
            self.buf = buf

            off = HDR_COMMON_OFF
            self.buf[off:off + SHA256_HASH_LEN] = tx_hash.binary
            off += SHA256_HASH_LEN
            struct.pack_into('<L', buf, off, sid)
            off += _SID_LEN
            self.buf[off:off + len(tx_val)] = tx_val
            off += len(tx_val)

            Message.__init__(self, 'tx', off - HDR_COMMON_OFF, buf)
        else:
            assert not isinstance(buf, str)
            self.buf = buf
            self._memoryview = memoryview(self.buf)

    def tx_hash(self):
        if self._tx_hash is None:
            off = HDR_COMMON_OFF
            self._tx_hash = ObjectHash(self._memoryview[off:off + SHA256_HASH_LEN])
        return self._tx_hash

    def short_id(self):
        if self._short_id is None:
            off = HDR_COMMON_OFF + SHA256_HASH_LEN
            self._short_id, = struct.unpack_from('<L', self.buf[off:off + _SID_LEN], 0)

        if self._short_id != _NULL_SID:
            return self._short_id

    def tx_val(self):
        if self._tx_val is None:
            off = HDR_COMMON_OFF + SHA256_HASH_LEN + _SID_LEN
            self._tx_val = self._memoryview[off:off + self.payload_len()]

        # TODO check for empty?
        return self._tx_val

    @staticmethod
    def peek_message(input_buffer):
        buf = input_buffer.peek_message(HDR_COMMON_OFF + SHA256_HASH_LEN)

        # FIXME statement does nothing, and returning false,none,none breaks tests
        # if len(buf) < HDR_COMMON_OFF + _BINARY_LEN:
        #     False, None, None
        _, length = struct.unpack_from('<12sL', buf, 0)
        msg_hash = ObjectHash(buf[HDR_COMMON_OFF:HDR_COMMON_OFF + SHA256_HASH_LEN])
        return True, msg_hash, length
