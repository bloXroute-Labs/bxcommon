import struct

from bxcommon.constants import BTC_HDR_COMMON_OFF, BTC_SHA_HASH_LEN
from bxcommon.messages.btc.btc_message import BTCMessage
from bxcommon.messages.btc.btc_messages_util import pack_int_to_btcvarint, btcvarint_to_int
from bxcommon.utils.object_hash import BTCObjectHash


class DataBTCMessage(BTCMessage):
    # FIXME hashes is sharing global state
    def __init__(self, magic=None, version=None, hashes=[],
                 hash_stop=None, command=None, buf=None):
        if buf is None:
            buf = bytearray(BTC_HDR_COMMON_OFF + 9 + (len(hashes) + 1) * 32)
            self.buf = buf

            off = BTC_HDR_COMMON_OFF
            struct.pack_into('<I', buf, off, version)
            off += 4
            off += pack_int_to_btcvarint(len(hashes), buf, off)

            for hash_val in hashes:
                buf[off:off + 32] = hash_val.get_big_endian()
                off += 32

            buf[off:off + 32] = hash_stop.get_big_endian()
            off += 32

            BTCMessage.__init__(self, magic, command, off - BTC_HDR_COMMON_OFF, buf)
        else:
            self.buf = buf
            self._memoryview = memoryview(buf)
            self._magic = self._command = self._payload_len = self._checksum = None
            self._payload = None

        self._version = self._hash_count = self._hashes = self._hash_stop = None

    def version(self):
        if self._version is None:
            self._version = struct.unpack_from('<I', self.buf, BTC_HDR_COMMON_OFF)
        return self._version

    def hash_count(self):
        if self._hash_count is None:
            raise RuntimeError('FIXME')
            # FIXME buf is not defined, should be self.buf, fix and test
            # off = BTC_HDR_COMMON_OFF + 4
            # self._hash_count, size = btcvarint_to_int(buf, off)

        return self._hash_count

    def __iter__(self):
        off = BTC_HDR_COMMON_OFF + 4  # For the version field.
        b_count, size = btcvarint_to_int(self.buf, off)
        off += size

        for i in xrange(b_count):
            yield BTCObjectHash(buf=self.buf, offset=off, length=BTC_SHA_HASH_LEN)
            off += 32

    def hash_stop(self):
        return BTCObjectHash(buf=self.buf, offset=BTC_HDR_COMMON_OFF + self.payload_len() - 32, length=BTC_SHA_HASH_LEN)


class GetHeadersBTCMessage(DataBTCMessage):
    # FIXME hashes is sharing global state
    def __init__(self, magic=None, version=None, hashes=[], hash_stop=None, buf=None):
        DataBTCMessage.__init__(self, magic, version, hashes, hash_stop, 'getheaders', buf)


class GetBlocksBTCMessage(DataBTCMessage):
    # FIXME hashes is sharing global state
    def __init__(self, magic=None, version=None, hashes=[], hash_stop=None, buf=None):
        DataBTCMessage.__init__(self, magic, version, hashes, hash_stop, 'getblocks', buf)