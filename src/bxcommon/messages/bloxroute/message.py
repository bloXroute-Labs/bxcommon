import struct

from bxcommon import constants
from bxcommon.exceptions import PayloadLenError
from bxcommon.messages.abstract_message import AbstractMessage
from bxcommon.utils import logger


class Message(AbstractMessage):
    HEADER_LENGTH = constants.HDR_COMMON_OFF

    def __init__(self, msg_type=None, payload_len=None, buf=None):
        if buf is None or len(buf) < self.HEADER_LENGTH:
            raise ValueError("Buffer must be at least {0} in length.".format(self.HEADER_LENGTH))

        if not (isinstance(payload_len, (int, long))):
            raise ValueError("Payload_len must be an integer or long.")

        if payload_len < 0:
            raise ValueError("Payload_len must be a positive integer.")

        if msg_type is None:
            raise ValueError("Msg_type must be defined.")

        self.buf = buf
        self._memoryview = memoryview(buf)

        off = 0
        struct.pack_into('<12sL', buf, off, msg_type, payload_len)
        off += 16

        self._msg_type = msg_type
        self._payload_len = payload_len
        self._payload = None

    # TODO: pull this out in to a message protocol
    @classmethod
    def unpack(cls, buf):
        command, payload_length = struct.unpack_from("<12sL", buf)
        return command.rstrip(constants.MSG_NULL_BYTE), payload_length

    @classmethod
    def validate_payload(cls, buf, unpacked_args):
        _command, payload_length = unpacked_args
        if payload_length != len(buf) - cls.HEADER_LENGTH:
            error_message = "Payload length does not match buffer size: {} vs {} bytes" \
                .format(payload_length, len(buf) - cls.HEADER_LENGTH)
            logger.error(error_message)
            raise PayloadLenError(error_message)

    @classmethod
    def initialize_class(cls, cls_type, buf, unpacked_args):
        command, payload_length = unpacked_args
        instance = cls_type(buf=buf)
        instance._msg_type = command
        instance._payload_len = payload_length
        return instance

    # END TODO

    def rawbytes(self):
        """
        Returns a memoryview of the message
        """
        if self._payload_len is None:
            self._payload_len, _ = struct.unpack_from('<L', self.buf, constants.MSG_TYPE_LEN)

        if self._payload_len + self.HEADER_LENGTH == len(self.buf):
            return self._memoryview
        else:
            return self._memoryview[0:self._payload_len + self.HEADER_LENGTH]

    def msg_type(self):
        if self._msg_type is None:
            self._msg_type = struct.unpack_from('<12s', self.buf)[0]
        return self._msg_type

    def payload_len(self):
        if self._payload_len is None:
            self._payload_len = struct.unpack_from('<L', self.buf, constants.MSG_TYPE_LEN)[0]
        return self._payload_len

    def payload(self):
        if self._payload is None:
            self._payload = self.buf[self.HEADER_LENGTH:self.payload_len() + self.HEADER_LENGTH]
        return self._payload

    def __eq__(self, other):
        """
        Expensive equality comparison. Use only for tests.
        """
        if not isinstance(other, Message):
            return False
        else:
            return self.rawbytes().tobytes() == other.rawbytes().tobytes()


