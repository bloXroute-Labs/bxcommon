from typing import Optional

from bxcommon import constants
from bxcommon.messages.bloxroute.bloxroute_message_control_flags import BloxrouteMessageControlFlags
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.validation.abstract_message_validator import AbstractMessageValidator
from bxcommon.messages.validation.message_size_validation_settings import MessageSizeValidationSettings
from bxcommon.messages.validation.message_validation_error import MessageValidationError
from bxcommon.utils import convert
from bxcommon.utils.buffers.input_buffer import InputBuffer


class BloxrouteMessageValidator(AbstractMessageValidator):
    STARTING_SEQUENCE_CONTROL_FLAGS_FIRST_VERSION = 4

    def __init__(self, size_validation_settings: Optional[MessageSizeValidationSettings],
                 connection_protocol_version: int):
        self._size_validation_settings: Optional[MessageSizeValidationSettings] = size_validation_settings
        self._connection_protocol_version: int = connection_protocol_version

    def validate(self, is_full_msg: bool, msg_type: str, header_len: int, payload_len: int,
                 input_buffer: InputBuffer) -> None:
        """
        Validates message payload length.
        Throws MessageValidationError is message is not valid

        :param is_full: indicates if the full message is available on input buffer
        :param msg_type: message type
        :param header_len: message header length
        :param payload_len: message payload length
        :param input_buffer: input buffer
        """

        if self._connection_protocol_version >= self.STARTING_SEQUENCE_CONTROL_FLAGS_FIRST_VERSION:
            self._validate_starting_sequence(input_buffer)

        if self._size_validation_settings is not None:
            self._validate_payload_length(msg_type, payload_len)

        if self._connection_protocol_version >= self.STARTING_SEQUENCE_CONTROL_FLAGS_FIRST_VERSION:
            self._validate_control_flags(is_full_msg, header_len, payload_len, input_buffer)

    def _validate_starting_sequence(self, input_buffer: InputBuffer) -> None:

        if input_buffer.length < constants.STARTING_SEQUENCE_BYTES_LEN:
            return

        if input_buffer[:constants.STARTING_SEQUENCE_BYTES_LEN] != constants.STARTING_SEQUENCE_BYTES:
            raise MessageValidationError(
                "Expected message to begin with starting sequence but received first bytes '{}'"
                    .format(convert.bytes_to_hex(input_buffer[:constants.STARTING_SEQUENCE_BYTES_LEN])))

    def _validate_payload_length(self, msg_type: str, payload_len: int) -> None:
        if msg_type is None or payload_len is None:
            return

        if msg_type == BloxrouteMessageType.TRANSACTION:
            assert self._size_validation_settings is not None
            if payload_len > self._size_validation_settings.max_tx_size_bytes:
                raise MessageValidationError(
                    "Transaction message size exceeds expected max size. Expected: {}. Actual: {}."
                        .format(self._size_validation_settings.max_tx_size_bytes, payload_len))

        elif msg_type == BloxrouteMessageType.BROADCAST or msg_type == BloxrouteMessageType.TRANSACTIONS or \
                msg_type == BloxrouteMessageType.TX_SERVICE_SYNC_BLOCKS_SHORT_IDS or \
                msg_type == BloxrouteMessageType.TX_SERVICE_SYNC_TXS or \
                msg_type == BloxrouteMessageType.TRANSACTION_CLEANUP or \
                msg_type == BloxrouteMessageType.BLOCK_CONFIRMATION:
            assert self._size_validation_settings is not None
            if payload_len > self._size_validation_settings.max_block_size_bytes:
                raise MessageValidationError("{} message size exceeds expected max size. Expected: {}. Actual: {}."
                                             .format(msg_type, self._size_validation_settings.max_block_size_bytes,
                                                     payload_len))

        elif payload_len > constants.DEFAULT_MAX_PAYLOAD_LEN_BYTES:
            raise MessageValidationError("Message by type '{}' exceeds expected payload len. Expected: {}. Actual: {}."
                                         .format(msg_type, constants.DEFAULT_MAX_PAYLOAD_LEN_BYTES, payload_len))

    def _validate_control_flags(self, is_full: bool, header_len: int, payload_len: int,
                                input_buffer: InputBuffer) -> None:
        if not is_full:
            return

        if input_buffer.length < header_len + payload_len:
            raise MessageValidationError(
                "Not enough bytes in the input buffer to get control flags. Header length: {}. Payload length: {}. Input buffer length: {}".format(
                    header_len, payload_len, input_buffer.length))

        control_flag_byte = input_buffer[header_len + payload_len - 1:header_len + payload_len]

        if not control_flag_byte[0] & BloxrouteMessageControlFlags.VALID:
            raise MessageValidationError(
                "Control flags byte does not have VALID flag set. Value: {}.".format(control_flag_byte))
