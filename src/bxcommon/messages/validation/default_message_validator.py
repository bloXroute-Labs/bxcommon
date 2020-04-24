from bxcommon.messages.validation.abstract_message_validator import AbstractMessageValidator
from bxcommon.utils.buffers.input_buffer import InputBuffer


class DefaultMessageValidator(AbstractMessageValidator):

    def validate(
        self,
        is_full_msg: bool,
        msg_type: str,
        header_len: int,
        payload_len: int,
        input_buffer: InputBuffer
    ) -> None:
        """
        Validates message payload length.
        Throws MessageValidationError is message is not valid

        :param is_full: indicates if the full message is available on input buffer
        :param msg_type: message type
        :param header_len: message header length
        :param payload_len: message payload length
        :param input_buffer: input buffer
        """
