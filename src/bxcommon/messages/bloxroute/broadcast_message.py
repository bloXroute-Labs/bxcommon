import struct
from typing import Optional

from bxcommon import constants
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.messages.bloxroute.abstract_broadcast_message import AbstractBroadcastMessage
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.utils import crypto
from bxcommon.utils.buffers.input_buffer import InputBuffer
from bxcommon.utils.object_hash import Sha256Hash
from bxutils.logging.log_level import LogLevel


class BroadcastMessage(AbstractBroadcastMessage):
    MESSAGE_TYPE = BloxrouteMessageType.BROADCAST

    def __init__(self, message_hash: Optional[Sha256Hash] = None, network_num: Optional[int] = None,
                 source_id: str = "", is_encrypted: bool = False, blob: Optional[bytearray] = None,
                 buf: Optional[bytearray] = None):
        self._block_id = None
        self._is_encrypted = None
        self._blob = None

        # override payload length for variable length message
        if blob:
            self.PAYLOAD_LENGTH = AbstractBroadcastMessage.PAYLOAD_LENGTH + constants.BLOCK_ENCRYPTED_FLAG_LEN \
                                  + len(blob)
        super().__init__(message_hash, network_num, source_id, buf)

        if buf is None:
            # minus control flag
            off = self.HEADER_LENGTH + AbstractBroadcastMessage.PAYLOAD_LENGTH - constants.CONTROL_FLAGS_LEN

            struct.pack_into("?", self.buf, off, is_encrypted)
            off += constants.BLOCK_ENCRYPTED_FLAG_LEN

            self.buf[off:off + len(blob)] = blob

    def log_level(self):
        return LogLevel.INFO

    def is_encrypted(self) -> bool:
        if self._is_encrypted is None:
            off = self.HEADER_LENGTH + AbstractBroadcastMessage.PAYLOAD_LENGTH - constants.CONTROL_FLAGS_LEN
            self._is_encrypted, = struct.unpack_from("?", self.buf, off)
        return self._is_encrypted

    def block_hash(self) -> Sha256Hash:
        return self.message_hash()

    def blob(self) -> memoryview:
        if self._blob is None:
            off = self.HEADER_LENGTH + AbstractBroadcastMessage.PAYLOAD_LENGTH + constants.BLOCK_ENCRYPTED_FLAG_LEN - \
                  constants.CONTROL_FLAGS_LEN
            self._blob = self._memoryview[off:self.HEADER_LENGTH + self.payload_len() - constants.CONTROL_FLAGS_LEN]

        return self._blob

    @classmethod
    def peek_network_num(cls, input_buffer: InputBuffer):
        off = AbstractBloxrouteMessage.HEADER_LENGTH + crypto.SHA256_HASH_LEN

        if input_buffer.length < off + constants.NETWORK_NUM_LEN:
            raise ValueError("Not enough bytes to peek network number.")

        network_num_bytes = input_buffer.peek_message(off + constants.NETWORK_NUM_LEN)

        network_num, = struct.unpack_from("<L", network_num_bytes, off)

        return network_num

    def __repr__(self):
        return "BroadcastMessage<network_num: {}, block_id: {}, blob_length: {}, is_encrypted: {}, source_id: {}>" \
            .format(self.network_num(), self.message_id(), len(self.blob()), self.is_encrypted(), self.source_id())
