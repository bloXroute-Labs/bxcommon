import struct
from bxcommon.constants import SHA256_HASH_LEN
# Used to take the last few characters of the SHA256 encryption as the hash function.
# This is done because using the last characters of the SHA256 function provides major speed boosts.
PARTIAL_HASH_LENGTH = 4


#FIXME refactor to dedup code
class ObjectHash(object):
    # binary is a memoryview or a bytearray
    # we do not intend for the binary to mutate
    def __init__(self, binary):
        #
        assert len(binary) == SHA256_HASH_LEN

        self.binary = binary
        if isinstance(self.binary, memoryview):
            self.binary = bytearray(binary)

        self._hash = struct.unpack("<L", self.binary[-PARTIAL_HASH_LENGTH:])[0]

    def __hash__(self):
        return self._hash

    def __cmp__(self, id1):
        if id1 is None or self.binary < id1.binary:
            return -1
        elif self.binary > id1.binary:
            return 1
        return 0

    def __repr__(self):
        return repr(self.binary)

    def __getitem__(self, arg):
        return self.binary.__getitem__(arg)


class BTCObjectHash(object):
    def __init__(self, buf=None, offset=0, length=0, binary=None):
        assert (binary is not None and len(binary) == 32) or (length == 32 and len(buf) >= offset + length)
        if buf is not None:
            if isinstance(buf, bytearray):
                self.binary = buf[offset:offset + length]
            else:  # In case this is a memoryview.
                self.binary = bytearray(buf[offset:offset + length])
            self.binary = self.binary[::-1]
        elif binary is not None:
            if isinstance(binary, memoryview):
                self.binary = bytearray(binary)
            else:
                self.binary = binary
        else:
            raise ValueError('No data was passed')

        # This is where the big endian format will be stored
        self._buf = None
        self._hash = struct.unpack("<L", self.binary[-PARTIAL_HASH_LENGTH:])[0]
        self._full_str = None

    def __hash__(self):
        return self._hash

    def __cmp__(self, id1):
        if id1 is None or self.binary < id1.binary:
            return -1
        elif self.binary > id1.binary:
            return 1
        return 0

    def __repr__(self):
        return repr(self.binary)

    def __getitem__(self, arg):
        return self.binary.__getitem__(arg)

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
