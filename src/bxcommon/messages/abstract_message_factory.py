from abc import ABCMeta

from bxcommon.exceptions import ParseError, UnrecognizedCommandError


class AbstractMessageFactory(object):
    """
    Message factory abstract base class.

    Unpacks buffer content based on subclass implementations, pulling out the command type string and loading the
    message type class from the loader.
    """

    __metaclass__ = ABCMeta

    def __init__(self):
        self.base_message_type = None
        self.message_type_mapping = {}

    def get_message_header_preview_from_input_buffer(self, input_buffer):
        """
        Peeks at a message on the input buffer, determining if its full.
        Returns (is_full_message, command, payload_length)
        """
        if input_buffer.length < self.base_message_type.HEADER_LENGTH:
            return False, None, None
        else:
            unpacked_args = self.base_message_type.unpack(input_buffer[:self.base_message_type.HEADER_LENGTH])
            command = unpacked_args[0]
            payload_length = unpacked_args[-1]
            is_full_message = input_buffer.length >= payload_length + self.base_message_type.HEADER_LENGTH
            return is_full_message, command, payload_length

    def create_message_from_buffer(self, buf):
        """
        Parses a full message from a buffer based on its command into one of the loaded message types.
        """
        if len(buf) < self.base_message_type.HEADER_LENGTH:
            raise ParseError("Message was too short to be parsed. Raw data: {0}".format(buf))

        unpacked_args = self.base_message_type.unpack(buf)
        self.base_message_type.validate_payload(buf, unpacked_args)

        command = unpacked_args[0]
        if command not in self.message_type_mapping:
            raise UnrecognizedCommandError("Message not recognized: {0}. Raw data: {1}".format(command, repr(buf)), buf)

        return self.create_message(command, buf, unpacked_args)

    def create_message(self, command, buf, args=None):
        message_cls = self.message_type_mapping[command]
        return self.base_message_type.initialize_class(message_cls, buf, args)
