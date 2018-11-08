import struct

from bxcommon.utils.crypto import SHA256_HASH_LEN

# Used to take the last few characters of the SHA256 encryption as the hash function.
# This is done because using the last characters of the SHA256 function provides major speed boosts.
PARTIAL_HASH_LENGTH = 4


class ObjectHash(object):
    # binary is a memoryview or a bytearray
    # we do not intend for the binary to mutate
    def __init__(self, binary):
        #
        if len(binary) != SHA256_HASH_LEN:
            raise ValueError("Binary has the wrong length.")

        self.binary = bytearray(binary) if isinstance(binary, memoryview) else binary

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


class BTCObjectHash(ObjectHash):
    def __init__(self, buf=None, offset=0, length=0, binary=None):

        from_binary = binary is not None and len(binary) == SHA256_HASH_LEN
        from_buf = length == SHA256_HASH_LEN and len(buf) >= offset + length

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

        super(BTCObjectHash, self).__init__(local_binary)

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
