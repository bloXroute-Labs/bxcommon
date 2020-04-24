from bxcommon.messages.abstract_internal_message import AbstractInternalMessage
from bxcommon.messages.versioning.abstract_message_converter import AbstractMessageConverter


class _NoChangesMessageConverter(AbstractMessageConverter):

    def convert_to_older_version(self, msg: AbstractInternalMessage) -> AbstractInternalMessage:
        return msg

    def convert_from_older_version(self, msg: AbstractInternalMessage) -> AbstractInternalMessage:
        return msg

    def convert_first_bytes_to_older_version(self, first_msg_bytes):
        return first_msg_bytes

    def convert_first_bytes_from_older_version(self, first_msg_bytes):
        return first_msg_bytes

    def convert_last_bytes_to_older_version(self, last_msg_bytes):
        return last_msg_bytes

    def convert_last_bytes_from_older_version(self, last_msg_bytes):
        return last_msg_bytes

    def get_message_size_change_to_older_version(self):
        return 0

    def get_message_size_change_from_older_version(self):
        return 0


no_changes_message_converter = _NoChangesMessageConverter()
