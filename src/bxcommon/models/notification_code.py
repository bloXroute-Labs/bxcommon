from enum import IntEnum


class NotificationCodeRange(IntEnum):
    DEBUG = 2000  # <2000
    INFO = 4000  # <4000
    WARNING = 6000  # <6000
    ERROR = 8000  # <8000


class NotificationCode(IntEnum):
    QUOTA_DEPLETED = 4400
    QUOTA_DEPLETED_TX_BLOCKED = 4401
    QUOTA_DEPLETED_TX_HANDLED_AS_FREE = 4402
    QUOTA_NOT_SET_TX_HANDLED_AS_FREE = 4403

# notifications are being formatted according to the provided format string
# the formatting arguments (list) are as follows
#
# 0    - notification code number
# 1    - notification code label
# 2..n -  notification content items in order, content is treated as csv


default_notification_format = "{1}({0}): {2}"

NotificationFormatting = {
    NotificationCode.QUOTA_DEPLETED: default_notification_format,
    NotificationCode.QUOTA_DEPLETED_TX_BLOCKED: default_notification_format,
    NotificationCode.QUOTA_DEPLETED_TX_HANDLED_AS_FREE: default_notification_format,
    NotificationCode.QUOTA_NOT_SET_TX_HANDLED_AS_FREE: default_notification_format,
}
