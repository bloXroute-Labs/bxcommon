from abc import abstractmethod, ABCMeta
from typing import Optional

from bxcommon.utils.buffers.input_buffer import InputBuffer


class AbstractMessageValidator:
    """
    Base class for message validators.
    Checks correctness of the message on different stages of processing
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def validate(
        self,
        is_full_msg: bool,
        msg_type: Optional[bytes],
        header_len: int,
        payload_len: Optional[int],
        input_buffer: InputBuffer
    ) -> None:
        """
        Validates message payload length.
        Throws MessageValidationError is message is not valid

        :param is_full_msg: indicates if the full message is available on input buffer
        :param msg_type: message type
        :param header_len: message header length
        :param payload_len: message payload length
        :param input_buffer: input buffer
        """
