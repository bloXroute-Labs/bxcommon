import struct
from typing import Optional

from bxcommon import constants
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.messages.bloxroute.abstract_broadcast_message import AbstractBroadcastMessage
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.models.broadcast_message_type import BroadcastMessageType
from bxcommon.utils import crypto
from bxcommon.utils.buffers.input_buffer import InputBuffer
from bxcommon.utils.object_hash import Sha256Hash, ConcatHash
from bxutils.logging.log_level import LogLevel


class BroadcastMessage(AbstractBroadcastMessage):
    MESSAGE_TYPE = BloxrouteMessageType.BROADCAST

    def __init__(self, message_hash: Optional[Sha256Hash] = None, network_num: Optional[int] = None,
                 source_id: str = "", broadcast_type: BroadcastMessageType = BroadcastMessageType.BLOCK,
                 is_encrypted: bool = False, blob: Optional[bytearray] = None, buf: Optional[bytearray] = None):
        self._block_id = None
        self._is_encrypted = None
        self._blob = None
        self._broadcast_type: Optional[BroadcastMessageType] = None
        self._block_hash_with_broadcast_type: Optional[ConcatHash] = None

        # override payload length for variable length message
        if blob:
            # pylint: disable=invalid-name
            self.PAYLOAD_LENGTH = (
                AbstractBroadcastMessage.PAYLOAD_LENGTH
                + constants.BROADCAST_TYPE_LEN
                + constants.BLOCK_ENCRYPTED_FLAG_LEN +
                len(blob)
            )
        super().__init__(message_hash, network_num, source_id, buf)

        if buf is None:
            # minus control flag
            off = self.HEADER_LENGTH + AbstractBroadcastMessage.PAYLOAD_LENGTH - constants.CONTROL_FLAGS_LEN

            struct.pack_into("<4s", self.buf, off, broadcast_type.value.encode(constants.DEFAULT_TEXT_ENCODING))
            off += constants.BROADCAST_TYPE_LEN
            struct.pack_into("?", self.buf, off, is_encrypted)
            off += constants.BLOCK_ENCRYPTED_FLAG_LEN

            # pyre-fixme[6]: Expected `Sized` for 1st param but got
            #  `Optional[bytearray]`.
            self.buf[off:off + len(blob)] = blob

    def __repr__(self) -> str:
        return (
            f"BroadcastMessage<"
            f"network_num: {self.network_num()}, "
            f"message_id: {self.message_id()}, "
            f"blob_length: {len(self.blob())}, "
            f"broadcast_type: {self.broadcast_type().value}, "
            f"is_encrypted: {self.is_encrypted()}, "
            f"source_id: {self.source_id_as_str()}"
            f">"
        )

    def log_level(self) -> LogLevel:
        return LogLevel.DEBUG

    def broadcast_type(self) -> BroadcastMessageType:
        if self._broadcast_type is None:
            off = self.HEADER_LENGTH + AbstractBroadcastMessage.PAYLOAD_LENGTH - constants.CONTROL_FLAGS_LEN
            broadcast_type_in_str = struct.unpack_from("<4s", self.buf, off)[0].decode(constants.DEFAULT_TEXT_ENCODING)
            self._broadcast_type = BroadcastMessageType(broadcast_type_in_str)

        broadcast_type = self._broadcast_type
        assert broadcast_type is not None
        return broadcast_type

    def is_encrypted(self) -> bool:
        if self._is_encrypted is None:
            off = self.HEADER_LENGTH + AbstractBroadcastMessage.PAYLOAD_LENGTH + constants.BROADCAST_TYPE_LEN \
                  - constants.CONTROL_FLAGS_LEN
            self._is_encrypted, = struct.unpack_from("?", self.buf, off)
        # pyre-fixme[7]: Expected `bool` but got `None`.
        return self._is_encrypted

    def message_id(self) -> ConcatHash:
        """
        Concatenated hash, includes block hash, network number and broadcast type.
        """
        if self._block_hash_with_broadcast_type is None:
            off = self.HEADER_LENGTH
            original_block_hash_with_network_num = self.buf[
                                                   off:off + crypto.SHA256_HASH_LEN + constants.NETWORK_NUM_LEN
                                                   ]
            off += AbstractBroadcastMessage.PAYLOAD_LENGTH - constants.CONTROL_FLAGS_LEN
            broadcast_type_bytearray = self.buf[off:off + constants.BROADCAST_TYPE_LEN]
            self._block_hash_with_broadcast_type = ConcatHash(
                original_block_hash_with_network_num + broadcast_type_bytearray, 0
            )

        block_hash_with_broadcast_type = self._block_hash_with_broadcast_type
        assert block_hash_with_broadcast_type is not None
        return block_hash_with_broadcast_type

    def block_hash(self) -> Sha256Hash:
        return super().message_hash()

    def blob(self) -> memoryview:
        if self._blob is None:
            off = self.HEADER_LENGTH + AbstractBroadcastMessage.PAYLOAD_LENGTH + constants.BROADCAST_TYPE_LEN + \
                  constants.BLOCK_ENCRYPTED_FLAG_LEN - constants.CONTROL_FLAGS_LEN
            self._blob = self._memoryview[off:self.HEADER_LENGTH + self.payload_len() - constants.CONTROL_FLAGS_LEN]

        # pyre-fixme[7]: Expected `memoryview` but got `None`.
        return self._blob

    @classmethod
    def peek_network_num(cls, input_buffer: InputBuffer) -> int:
        off = AbstractBloxrouteMessage.HEADER_LENGTH + crypto.SHA256_HASH_LEN

        if input_buffer.length < off + constants.NETWORK_NUM_LEN:
            raise ValueError("Not enough bytes to peek network number.")

        network_num_bytes = input_buffer.peek_message(off + constants.NETWORK_NUM_LEN)

        network_num, = struct.unpack_from("<L", network_num_bytes, off)

        return network_num
