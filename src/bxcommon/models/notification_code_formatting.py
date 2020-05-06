from bxcommon.models.notification_code import NotificationCode

# notifications are being formatted according to the provided format string
# the formatting arguments (list) are as follows
#

# 0    - notification code number
# 1    - notification code label
# 2..n -  notification content items in order, content is treated as csv
default_notification_format = "{1}({0}): {2}"

# {percentage}% of {quota_type} daily {entity_type} quota with limit of {limit} {entity_type}s per day is depleted.
quota_notification_format = "{0}% of {1} daily {2} quota with limit of {3} {2}s per day is depleted."

NotificationFormatting = {
    NotificationCode.QUOTA_FILL_STATUS: quota_notification_format
}
