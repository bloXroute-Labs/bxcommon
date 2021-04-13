from bxutils.log_message_categories import PROCESSING_FAILED_CATEGORY, GENERAL_CATEGORY, EXCEPTION_OR_CANCELLATION
from bxutils.logging_messages_utils import LogMessage

COULD_NOT_SERIALIZE_FEED_ENTRY = LogMessage(
    "C-000079",
    PROCESSING_FAILED_CATEGORY,
    "Could not serialize feed entry. Skipping."
)

BAD_FEED_SUBSCRIBER = LogMessage(
    "C-000068",
    GENERAL_CATEGORY,
    "Subscriber {} was not receiving messages and emptying its queue from "
    "{}. Disconnecting.",
)
COULD_NOT_DESERIALIZE_TRANSACTION = LogMessage(
    "C-000069",
    PROCESSING_FAILED_CATEGORY,
    "Could not deserialize transaction in transaction service to Ethereum payload: {}, body: {}. Error: {}",
)
BAD_FEED_SUBSCRIBER_SHOULD_EXIT = LogMessage(
    "C-000070",
    GENERAL_CATEGORY,
    "Subscriber {} was not filtering messages correctly from "
    "{}. Disconnecting.",
)
CONNECTION_DOES_NOT_EXIST = LogMessage(
    "C-000071",
    EXCEPTION_OR_CANCELLATION,
    "Connection doesn't exist, cancelling {} "
)
