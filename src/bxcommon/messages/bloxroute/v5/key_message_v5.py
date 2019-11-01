import struct

from bxcommon import constants
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.utils import crypto
from bxcommon.utils.object_hash import Sha256Hash, ConcatHash
from bxutils.logging.log_level import LogLevel


class KeyMessageV5(AbstractBloxrouteMessage):
    MESSAGE_TYPE = BloxrouteMessageType.KEY

    def __init__(self, msg_hash=None, network_num=None, key=None, buf=None):
        if buf is None:
            assert len(key) == crypto.KEY_SIZE
            self.buf = bytearray(
                self.HEADER_LENGTH + crypto.SHA256_HASH_LEN + crypto.KEY_SIZE + constants.NETWORK_NUM_LEN + constants.CONTROL_FLAGS_LEN)

            off = self.HEADER_LENGTH
            self.buf[off:off + crypto.SHA256_HASH_LEN] = msg_hash.binary
            off += crypto.SHA256_HASH_LEN
            struct.pack_into("<L", self.buf, off, network_num)
            off += constants.NETWORK_NUM_LEN
            self.buf[off:off + crypto.KEY_SIZE] = key
            off += crypto.KEY_SIZE

            # Control flags are empty by default
            off += constants.CONTROL_FLAGS_LEN

            super(KeyMessageV5, self).__init__(self.MESSAGE_TYPE, off - self.HEADER_LENGTH, self.buf)
        else:
            assert not isinstance(buf, str)
            self.buf = buf
            self._memoryview = memoryview(self.buf)

        self._key = None
        self._block_id = None
        self._network_num = None
        self._block_hash = None
        self._payload_len = None
        self._payload = None

    def log_level(self):
        return LogLevel.DEBUG

    def block_hash(self):
        """
        The hash of the data block that is being returned.
        """
        if self._block_hash is None:
            off = self.HEADER_LENGTH
            self._block_hash = Sha256Hash(self._memoryview[off:off + crypto.SHA256_HASH_LEN])
        return self._block_hash

    def block_id(self):
        if self._block_id is None:
            off = self.HEADER_LENGTH
            # Hash over the SHA256 hash and the network number.
            self._block_id = ConcatHash(self._memoryview[off:off + crypto.SHA256_HASH_LEN + constants.NETWORK_NUM_LEN],
                                        0)
        return self._block_id

    def network_num(self):
        if self._network_num is None:
            off = self.HEADER_LENGTH + crypto.SHA256_HASH_LEN
            self._network_num, = struct.unpack_from("<L", self.buf, off)

        return self._network_num

    def key(self):
        if self._key is None:
            off = self.HEADER_LENGTH + crypto.SHA256_HASH_LEN + constants.NETWORK_NUM_LEN
            self._key = self._memoryview[off:off + crypto.KEY_SIZE]
        return self._key

    def __repr__(self):
        return "KeyMessage<network_num: {}, block_id: {}".format(self.network_num(),
                                                                 self.block_id())
