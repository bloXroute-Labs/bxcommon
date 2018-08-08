import struct


class ObjectHash(object):
    # binary is a memoryview or a bytearray
    def __init__(self, binary):
        assert len(binary) == 32

        self.binary = binary
        if isinstance(self.binary, memoryview):
            self.binary = bytearray(binary)

        self._hash = struct.unpack("<L", self.binary[-4:])[0]

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
        if buf is not None:
            if isinstance(buf, bytearray):
                self.binary = buf[offset:offset + length]
            else:  # In case this is a memoryview.
                self.binary = bytearray(buf[offset:offset + length])
            self.binary = self.binary[::-1]
        else:
            self.binary = binary

        # This is where the big endian format will be stored
        self._buf = None
        self._hash = struct.unpack("<L", self.binary[-4:])[0]
        self._full_str = None

    def __hash__(self):
        return self._hash

    def __cmp__(self, id1):
        if id1 is None or self.binary > id1.binary:
            return -1
        elif self.binary < id1.binary:
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
