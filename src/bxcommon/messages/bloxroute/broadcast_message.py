import struct

from bxutils.logging.log_level import LogLevel

from bxcommon import constants
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.utils.buffers.input_buffer import InputBuffer
from bxcommon.utils.crypto import SHA256_HASH_LEN
from bxcommon.utils.object_hash import Sha256Hash, ConcatHash


class BroadcastMessage(AbstractBloxrouteMessage):
    MESSAGE_TYPE = BloxrouteMessageType.BROADCAST

    def __init__(self, msg_hash=None, network_num=None, is_encrypted=False, blob=None, buf=None):
        if buf is None:
            msg_buf = bytearray(
                self.HEADER_LENGTH + SHA256_HASH_LEN + constants.NETWORK_NUM_LEN + constants.BLOCK_ENCRYPTED_FLAG_LEN + len(
                    blob) + constants.CONTROL_FLAGS_LEN)

            off = self.HEADER_LENGTH
            msg_buf[off:off + SHA256_HASH_LEN] = msg_hash.binary
            off += SHA256_HASH_LEN
            struct.pack_into("<L", msg_buf, off, network_num)
            off += constants.NETWORK_NUM_LEN
            struct.pack_into("?", msg_buf, off, is_encrypted)
            off += constants.BLOCK_ENCRYPTED_FLAG_LEN

            msg_buf[off:off + len(blob)] = blob
            off += len(blob)

            # Control flags are empty by default
            off += constants.CONTROL_FLAGS_LEN

            super(BroadcastMessage, self).__init__(self.MESSAGE_TYPE, off - self.HEADER_LENGTH, msg_buf)
        else:
            assert not isinstance(buf, str)
            self.buf = buf
            self._memoryview = memoryview(self.buf)

        self._block_id = None
        self._block_hash = None
        self._network_num = None
        self._is_encrypted = None
        self._blob = None
        self._payload = None
        self._payload_len = None

    def log_level(self):
        return LogLevel.INFO

    def block_hash(self):
        """
        The hash of the data block that is being returned.
        """
        if self._block_hash is None:
            off = self.HEADER_LENGTH
            self._block_hash = Sha256Hash(self._memoryview[off:off + SHA256_HASH_LEN])
        return self._block_hash

    def block_id(self):
        if self._block_id is None:
            off = self.HEADER_LENGTH
            # Hash over the SHA256 hash and the network number.
            self._block_id = ConcatHash(self._memoryview[off:off + SHA256_HASH_LEN + constants.NETWORK_NUM_LEN], 0)
        return self._block_id

    def network_num(self):
        if self._network_num is None:
            off = self.HEADER_LENGTH + SHA256_HASH_LEN
            self._network_num, = struct.unpack_from("<L", self.buf, off)

        return self._network_num

    def is_encrypted(self):
        if self._is_encrypted is None:
            off = self.HEADER_LENGTH + SHA256_HASH_LEN + constants.NETWORK_NUM_LEN
            self._is_encrypted, = struct.unpack_from("?", self.buf, off)
        return self._is_encrypted

    def blob(self):
        if self._blob is None:
            off = self.HEADER_LENGTH + SHA256_HASH_LEN + constants.NETWORK_NUM_LEN + constants.BLOCK_ENCRYPTED_FLAG_LEN
            self._blob = self._memoryview[off:self.HEADER_LENGTH + self.payload_len() - constants.CONTROL_FLAGS_LEN]

        return self._blob

    @classmethod
    def peek_network_num(cls, input_buffer):
        if not isinstance(input_buffer, InputBuffer):
            raise TypeError("Arg input_buffer expected type in InputBuffer but was {}".format(type(input_buffer)))

        off = AbstractBloxrouteMessage.HEADER_LENGTH + SHA256_HASH_LEN

        if input_buffer.length < off + constants.NETWORK_NUM_LEN:
            raise ValueError("Not enough bytes to peek network number.")

        network_num_bytes = input_buffer.peek_message(off + constants.NETWORK_NUM_LEN)

        network_num, = struct.unpack_from("<L", network_num_bytes, off)

        return network_num

    def __repr__(self):
        return "BroadcastMessage<network_num: {}, block_id: {}, blob_length: {}, is_encrypted: {}>" \
            .format(self.network_num(), self.block_id(), len(self.blob()), self.is_encrypted())
