import struct

from bxcommon.constants import HDR_COMMON_OFF
from bxcommon.exceptions import PayloadLenError, UnrecognizedCommandError
from bxcommon.messages import message_types_loader
from bxcommon.utils import logger


class Message(object):
    def __init__(self, msg_type=None, payload_len=None, buf=None):
        if buf is None or len(buf) < HDR_COMMON_OFF:
            raise ValueError("Buffer must be at least 16 in length.")

        if not isinstance(payload_len, int):
            raise ValueError("Payload_len must be an integer.")

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

    # Returns a memoryview of the message.
    def rawbytes(self):
        if self._payload_len is None:
            self._payload_len, _ = struct.unpack_from('<L', self.buf, 12)

        if self._payload_len + HDR_COMMON_OFF == len(self.buf):
            return self._memoryview
        else:
            return self._memoryview[0:self._payload_len + HDR_COMMON_OFF]

    def msg_type(self):
        return self._msg_type

    def payload_len(self):
        if self._payload_len is None:
            self._payload_len = struct.unpack_from('<L', self.buf, 12)[0]
        return self._payload_len

    def payload(self):
        if self._payload is None:
            self._payload = self.buf[HDR_COMMON_OFF:self.payload_len() + HDR_COMMON_OFF]
        return self._payload


# peek at message, return (is_a_full_message, msg_type, length)
# input_buffer is an instance of InputBuffer
def peek_message(input_buffer):
    buf = input_buffer.peek_message(HDR_COMMON_OFF)

    if len(buf) < HDR_COMMON_OFF:
        return False, None, None

    _msg_type, _payload_len = struct.unpack_from('<12sL', buf, 0)
    _msg_type = _msg_type.rstrip('\x00')
    if _payload_len <= input_buffer.length - HDR_COMMON_OFF:
        return True, _msg_type, _payload_len
    return False, _msg_type, _payload_len


# parse a full message
def parse(buf):
    if len(buf) < HDR_COMMON_OFF:
        return None

    _msg_type, _payload_len = struct.unpack_from('<12sL', buf, 0)
    _msg_type = _msg_type.rstrip('\x00')

    if _payload_len != len(buf) - HDR_COMMON_OFF:
        logger.error("Payload length does not match buffer size! Payload is %d. Buffer is %d bytes long" % (
            _payload_len, len(buf)))
        raise PayloadLenError(
            "Payload length does not match buffer size! Payload is %d. Buffer is %d bytes long" % (
                _payload_len, len(buf)))

    message_types = message_types_loader.get_message_types()
    if _msg_type not in message_types:
        raise UnrecognizedCommandError("%s message not recognized!" % (_msg_type,), "Raw data: %s" % (repr(buf),))

    cls = message_types[_msg_type]
    msg = cls(buf=buf)
    msg._msg_type, msg._payload_len = _msg_type, _payload_len
    return msg
