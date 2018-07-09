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
        if id1 is None or self.binary > id1.binary:
            return -1
        elif self.binary < id1.binary:
            return 1
        return 0

    def __repr__(self):
        return repr(self.binary)

    def __getitem__(self, arg):
        return self.binary.__getitem__(arg)