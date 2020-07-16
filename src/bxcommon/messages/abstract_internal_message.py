import struct

from bxcommon import constants
from bxcommon.exceptions import PayloadLenError
from bxcommon.messages.abstract_message import AbstractMessage
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxutils import logging

logger = logging.get_logger(__name__)


class AbstractInternalMessage(AbstractMessage):
    MESSAGE_TYPE = BloxrouteMessageType.ABSTRACT_INTERNAL
    HEADER_LENGTH = constants.BX_HDR_COMMON_OFF
    STARTING_BYTES_LEN = 0

    def __init__(self, msg_type: bytes, payload_len: int, buf: bytearray) -> None:

        if len(buf) < self.HEADER_LENGTH:
            raise ValueError("Buffer must be at least {0} in length.".format(self.HEADER_LENGTH))

        if payload_len < 0:
            raise ValueError("Payload_len must be a positive integer.")

        off = self.STARTING_BYTES_LEN
        struct.pack_into("<12sL", buf, off, msg_type, payload_len)
        off += constants.BX_HDR_COMMON_OFF

        self.buf = buf
        self._memoryview = memoryview(buf)

        self._msg_type = msg_type
        self._payload_len = payload_len
        self._payload = None
        self._priority = False

    # TODO: pull this out in to a message protocol
    @classmethod
    def unpack(cls, buf):
        command, payload_length = struct.unpack_from("<12sL", buf, cls.STARTING_BYTES_LEN)
        return command.rstrip(constants.MSG_NULL_BYTE), payload_length

    @classmethod
    def validate_payload(cls, buf, unpacked_args) -> None:
        _command, payload_length = unpacked_args
        if payload_length != len(buf) - cls.HEADER_LENGTH:
            error_message = "Payload length does not match buffer size: {} vs {} bytes" \
                .format(payload_length, len(buf) - cls.HEADER_LENGTH)
            logger.error(error_message)
            raise PayloadLenError(error_message)

    # pylint: disable=protected-access
    @classmethod
    def initialize_class(cls, cls_type, buf, unpacked_args):
        command, payload_length = unpacked_args
        instance = cls_type(buf=buf)
        instance._msg_type = command
        instance._payload_len = payload_length
        return instance

    # END TODO

    def rawbytes(self) -> memoryview:
        """
        Returns a memoryview of the message
        """
        if self._payload_len is None:
            self._payload_len, = struct.unpack_from("<L", self.buf, self.STARTING_BYTES_LEN + constants.MSG_TYPE_LEN)

        if self._payload_len + self.HEADER_LENGTH == len(self.buf):
            return self._memoryview
        else:
            return self._memoryview[0:self._payload_len + self.HEADER_LENGTH]

    def msg_type(self) -> bytes:
        if self._msg_type is None:
            self._msg_type = struct.unpack_from("<12s", self.buf, self.STARTING_BYTES_LEN)[0]
        return self._msg_type

    def payload_len(self) -> int:
        if self._payload_len is None:
            self._payload_len = struct.unpack_from("<L", self.buf, self.STARTING_BYTES_LEN + constants.MSG_TYPE_LEN)[0]
        return self._payload_len

    def payload(self):
        if self._payload is None:
            self._payload = self.buf[self.HEADER_LENGTH:self.payload_len() + self.HEADER_LENGTH]
        return self._payload

    def set_priority(self, high: bool) -> None:
        """
        Sets the priority of this message (to be high or low)
        :param high: True if this is high priority. False otherwise.
        """
        self._priority = high

    def get_priority(self) -> bool:
        return self._priority

    def __eq__(self, other) -> bool:
        """
        Expensive equality comparison. Use only for tests.
        """
        if not isinstance(other, AbstractInternalMessage):
            return False
        else:
            return self.rawbytes().tobytes() == other.rawbytes().tobytes()

    def __repr__(self) -> str:
        return "Message<type: {}, length: {}>".format(self.MESSAGE_TYPE, len(self.rawbytes()))
