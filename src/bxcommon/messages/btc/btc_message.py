import hashlib
import struct

from bxcommon.constants import BTC_HDR_COMMON_OFF, BTC_HEADER_MINUS_CHECKSUM, btc_magic_numbers
from bxcommon.exceptions import ChecksumError, PayloadLenError, UnrecognizedCommandError
from bxcommon.messages.message_types_loader import get_btc_message_types
from bxcommon.utils import logger

sha256 = hashlib.sha256


class BTCMessage(object):
    def __init__(self, magic=None, command=None, payload_len=None, buf=None):
        self.buf = buf
        self._memoryview = memoryview(buf)

        magic_num = magic if magic not in btc_magic_numbers else btc_magic_numbers[magic]
        checksum = sha256(
            sha256(self._memoryview[BTC_HDR_COMMON_OFF:payload_len + BTC_HDR_COMMON_OFF]).digest()).digest()

        off = 0
        struct.pack_into('<L12sL', buf, off, magic_num, command, payload_len)
        off += 20
        buf[off:off + 4] = checksum[0:4]

        self._magic = magic_num
        self._command = command
        self._payload_len = payload_len
        self._payload = None
        self._checksum = None

    # Returns a memoryview of the message.
    def rawbytes(self):
        if self._payload_len is None:
            self._payload_len = struct.unpack_from('<L', self.buf, 16)[0]

        if self._payload_len + BTC_HDR_COMMON_OFF == len(self.buf):
            return self._memoryview
        else:
            return self._memoryview[0:self._payload_len + BTC_HDR_COMMON_OFF]

    # peek at message, return (is_a_full_message, magic, command, length)
    # input_buffer is an instance of InputBuffer
    @staticmethod
    def peek_message(input_buffer):
        buf = input_buffer.peek_message(BTC_HEADER_MINUS_CHECKSUM)
        if len(buf) < BTC_HEADER_MINUS_CHECKSUM:
            return False, None, None

        _magic, _command, _payload_len = struct.unpack_from('<L12sL', buf, 0)
        _command = _command.rstrip('\x00')
        if _payload_len <= input_buffer.length - 24:
            return True, _command, _payload_len
        return False, _command, _payload_len

    # parse a full message
    @staticmethod
    def parse(buf):
        if len(buf) < BTC_HEADER_MINUS_CHECKSUM:
            return None

        _magic, _command, _payload_len = struct.unpack_from('<L12sL', buf, 0)
        _command = _command.rstrip('\x00')
        _checksum = buf[20:24]

        if _payload_len != len(buf) - 24:
            logger.error("Payload length does not match buffer size! Payload is %d. Buffer is %d bytes long" % (
                _payload_len, len(buf)))
            raise PayloadLenError(
                "Payload length does not match buffer size! Payload is %d. Buffer is %d bytes long" % (
                    _payload_len, len(buf)))

        if _checksum != sha256(sha256(
                buf[BTC_HDR_COMMON_OFF:_payload_len + BTC_HDR_COMMON_OFF]).digest()).digest()[0:4]:
            logger.error("Checksum for packet doesn't match!")
            raise ChecksumError("Checksum for packet doesn't match! ", "Raw data: %s" % repr(buf))

        message_types = get_btc_message_types()
        if _command not in message_types:
            raise UnrecognizedCommandError("%s message not recognized!" % (_command,), "Raw data: %s" % (repr(buf),))

        cls = message_types[_command]
        msg = cls(buf=buf)
        msg._magic, msg._command, msg._payload_len, msg._checksum = _magic, _command, _payload_len, _checksum
        return msg

    def magic(self):
        return self._magic

    def command(self):
        return self._command

    def payload_len(self):
        if self._payload_len is None:
            self._payload_len = struct.unpack_from('<L', self.buf, 16)[0]
        return self._payload_len

    def checksum(self):
        return self._checksum

    def payload(self):
        if self._payload is None:
            self._payload = self.buf[BTC_HDR_COMMON_OFF:self.payload_len() + BTC_HDR_COMMON_OFF]
        return self._payload

    @staticmethod
    def get_header_from_partial_buf(buf):
        return struct.unpack_from('Q12s<I', buf, 0)
