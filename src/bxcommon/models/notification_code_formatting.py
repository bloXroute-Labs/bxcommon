from bxcommon.models.notification_code import NotificationCode

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

    NotificationCode.QUOTA_DEPLETED_BLOCK: default_notification_format,
    NotificationCode.QUOTA_DEPLETED_BLOCK_BLOCKED: default_notification_format,
}
