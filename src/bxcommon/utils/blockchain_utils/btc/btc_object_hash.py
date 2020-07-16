import struct

from bxcommon.utils import convert
from bxcommon.utils.object_hash import Sha256Hash, PARTIAL_HASH_LENGTH
from bxcommon.utils.blockchain_utils.btc.btc_common_constants import BTC_SHA_HASH_LEN


class BtcObjectHash(Sha256Hash):
    def __init__(self, buf=None, offset=0, length=0, binary=None) -> None:

        from_binary = binary is not None and len(binary) == BTC_SHA_HASH_LEN
        from_buf = length == BTC_SHA_HASH_LEN and len(buf) >= offset + length

        if not (from_binary or from_buf):
            raise ValueError("Either binary or buf must contain data.")

        if buf is not None:
            if isinstance(buf, bytearray):
                local_binary = buf[offset:offset + length]
            else:  # In case this is a memoryview.
                local_binary = bytearray(buf[offset:offset + length])
            local_binary = local_binary[::-1]
        elif binary is not None:
            local_binary = binary
        else:
            raise ValueError("No data was passed")

        super(BtcObjectHash, self).__init__(local_binary)

        # This is where the big endian format will be stored
        self._buf = None
        self._hash = struct.unpack("<L", self.binary[-PARTIAL_HASH_LENGTH:])[0]
        self._full_str = None

    def full_string(self):
        if self._full_str is None:
            self._full_str = str(self.binary)
        return self._full_str

    def get_little_endian(self):
        return self.binary

    def get_big_endian(self):
        if self._buf is None:
            self._buf = self.binary[::-1]
        return self._buf

    def __repr__(self):
        return "BtcObjectHash<binary: {}>".format(convert.bytes_to_hex(self.binary))

    def __str__(self):
        return convert.bytes_to_hex(self.binary)


NULL_BTC_BLOCK_HASH = BtcObjectHash(binary=bytearray(BTC_SHA_HASH_LEN))
