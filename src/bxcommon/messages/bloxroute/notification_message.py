import struct
from typing import Union, Optional

from bxcommon import constants
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.models.entity_type_model import EntityType
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

    def __init__(self, notification_code: Optional[Union[NotificationCode, int]] = None, raw: Optional[str] = None,
                 buf: Optional[bytearray] = None):
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

        self.buf: Optional[bytearray] = buf
        self._raw: Optional[str] = None
        self._notification_code: Optional[NotificationCode] = None
        self._memoryview = memoryview(buf)
        super(NotificationMessage, self).__init__(self.MESSAGE_TYPE, payload_len, buf)

    def __repr__(self):
        return "NotificationMsg: {}".format(self.formatted_message())

    def notification_code(self) -> Union[NotificationCode, int]:
        if self._notification_code is None:
            self._unpack()
        notification_code = self._notification_code
        assert notification_code is not None
        return notification_code

    def raw_message(self) -> str:
        if self._raw is None:
            self._unpack()
        raw = self._raw
        assert raw is not None
        return raw

    def formatted_message(self) -> str:
        if self._notification_code is None:
            self._unpack()
        notification_code = self._notification_code
        assert notification_code is not None
        raw = self._raw

        if self._notification_code == NotificationCode.QUOTA_FILL_STATUS:
            assert raw is not None
            args_list = raw.split(",")
            args_list[1] = str(EntityType(int(args_list[1])))
            return NotificationFormatting[self._notification_code].format(*args_list)

        elif self._notification_code == NotificationCode.ACCOUNT_EXPIRED_NOTIFICATION:
            return NotificationFormatting[self._notification_code]

        elif self._notification_code in NotificationFormatting:
            assert raw is not None
            return NotificationFormatting[self._notification_code].format(
                notification_code.value,
                notification_code.name,
                *raw.split(",")
            )
        else:
            return "{}: {}".format(notification_code, raw)

    def level(self) -> LogLevel:
        if self._notification_code is None:
            self._unpack()
        notification_code = self._notification_code
        assert notification_code is not None

        if notification_code < NotificationCodeRange.DEBUG:
            return LogLevel.DEBUG
        elif notification_code < NotificationCodeRange.INFO:
            return LogLevel.INFO
        elif notification_code < NotificationCodeRange.WARNING:
            return LogLevel.WARNING
        else:
            return LogLevel.ERROR

    def log_level(self) -> LogLevel:
        return LogLevel.DEBUG

    def _unpack(self) -> None:
        buf = self.buf
        assert buf is not None

        off = AbstractBloxrouteMessage.HEADER_LENGTH
        notification_code, = struct.unpack_from("<H", buf, off)
        off += constants.UL_SHORT_SIZE_IN_BYTES

        if notification_code in [item.value for item in NotificationCode]:
            self._notification_code = NotificationCode(notification_code)
        else:
            self._notification_code = notification_code

        self._raw = buf[off:AbstractBloxrouteMessage.HEADER_LENGTH +
                             self.payload_len() - constants.CONTROL_FLAGS_LEN].decode()
