import struct

from bxcommon.utils import convert
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
        return "ObjectHash<binary: {}>".format(convert.bytes_to_hex(self.binary))

    def __getitem__(self, arg):
        return self.binary.__getitem__(arg)
