import struct
from typing import Union
from bxcommon import constants
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.models.notification_code import NotificationCode, NotificationCodeRange
from bxcommon.models.notification_code_formatting import NotificationFormatting
from bxutils.logging.log_level import LogLevel


class NotificationMessage(AbstractBloxrouteMessage):
    """
    BloXroute message that contains a notification message

    """
    BASE_PAYLOAD_LENGTH = AbstractBloxrouteMessage.HEADER_LENGTH + constants.UL_SHORT_SIZE_IN_BYTES +\
                          constants.CONTROL_FLAGS_LEN
    MESSAGE_TYPE = BloxrouteMessageType.NOTIFICATION

    def __init__(self, notification_code: Union[NotificationCode, int] = None, raw: str = None, buf=None):
        if buf is None:
            buffer_len = self.BASE_PAYLOAD_LENGTH + (len(raw) if raw is not None else 0)
            buf = bytearray(buffer_len)

            off = AbstractBloxrouteMessage.HEADER_LENGTH
            struct.pack_into("<H", buf, off, notification_code)
            off += constants.UL_SHORT_SIZE_IN_BYTES
            if raw is not None:
                raw_ = raw.encode()
                buf[off:off + len(raw_)] = raw_
        else:
            buffer_len = len(buf)

        payload_len = buffer_len - AbstractBloxrouteMessage.HEADER_LENGTH

        self.buf = buf
        self._raw = None
        self._notification_code = None
        self._memoryview = memoryview(buf)
        super(NotificationMessage, self).__init__(self.MESSAGE_TYPE, payload_len, buf)

    def __repr__(self):
        return "NotificationMsg: {}".format(self.formatted_message())

    def notification_code(self) -> Union[NotificationCode, int]:
        if self._notification_code is None:
            self._unpack()
        assert self._notification_code is not None
        return self._notification_code

    def raw_message(self) -> str:
        if self._raw is None:
            self._unpack()
        assert self._raw is not None
        return self._raw

    def formatted_message(self):
        if self._notification_code is None:
            self._unpack()
        if self._notification_code in NotificationFormatting:
            return NotificationFormatting[self._notification_code].format(
                self._notification_code.value,
                self._notification_code.name,
                *self._raw.split(",")
            )
        else:
            return "{}: {}".format(self._notification_code, self._raw)

    def level(self):
        if self._notification_code is None:
            self._unpack()
        assert self._notification_code is not None
        if self._notification_code < NotificationCodeRange.DEBUG:
            return LogLevel.DEBUG
        elif self._notification_code < NotificationCodeRange.INFO:
            return LogLevel.INFO
        elif self._notification_code < NotificationCodeRange.WARNING:
            return LogLevel.WARNING
        else:
            return LogLevel.ERROR

    def log_level(self):
        return LogLevel.DEBUG

    def _unpack(self):
        off = AbstractBloxrouteMessage.HEADER_LENGTH
        notification_code, = struct.unpack_from("<H", self.buf, off)
        off += constants.UL_SHORT_SIZE_IN_BYTES

        if notification_code in [item.value for item in NotificationCode]:
            self._notification_code = NotificationCode(notification_code)
        else:
            self._notification_code = notification_code
        self._raw = self.buf[off:AbstractBloxrouteMessage.HEADER_LENGTH +
                             self.payload_len() - constants.CONTROL_FLAGS_LEN].decode()
