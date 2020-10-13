from bxcommon.models.notification_code import NotificationCode

# notifications are being formatted according to the provided format string
# the formatting arguments (list) are as follows
#

# 0    - notification code number
# 1    - notification code label
# 2..n -  notification content items in order, content is treated as csv
default_notification_format = "{1}({0}): {2}"

# {percentage}% of daily {entity_type} quota with limit of {limit} {entity_type}s per day is depleted.
quota_notification_format = "{0}% of daily {1} quota with limit of {2} {1}s per day is depleted."
account_expired_notification_format = "The account associated with this gateway has expired. " \
                                      "Please visit https://portal.bloxroute.com to renew your subscription."

NotificationFormatting = {
    NotificationCode.QUOTA_FILL_STATUS: quota_notification_format,
    NotificationCode.ACCOUNT_EXPIRED_NOTIFICATION: account_expired_notification_format
}
