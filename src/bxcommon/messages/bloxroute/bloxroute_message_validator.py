from typing import Optional

from bxcommon import constants
from bxcommon.messages.bloxroute.bloxroute_message_control_flags import BloxrouteMessageControlFlags
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.validation.abstract_message_validator import AbstractMessageValidator
from bxcommon.messages.validation.control_flag_validation_error import ControlFlagValidationError
from bxcommon.messages.validation.message_size_validation_settings import \
    MessageSizeValidationSettings
from bxcommon.messages.validation.message_validation_error import MessageValidationError
from bxcommon.utils import convert
from bxcommon.utils.buffers.input_buffer import InputBuffer


class BloxrouteMessageValidator(AbstractMessageValidator):
    FIRST_VALIDATING_VERSION = 4

    def __init__(
        self,
        size_validation_settings: Optional[MessageSizeValidationSettings],
        connection_protocol_version: int
    ):
        self._size_validation_settings: Optional[MessageSizeValidationSettings] = size_validation_settings
        self._connection_protocol_version: int = connection_protocol_version

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

        if self._connection_protocol_version >= self.FIRST_VALIDATING_VERSION:
            self._validate_starting_sequence(input_buffer)

        if self._size_validation_settings is not None:
            self._validate_payload_length(msg_type, payload_len)

        if self._connection_protocol_version >= self.FIRST_VALIDATING_VERSION:
            self._validate_control_flags(is_full_msg, header_len, payload_len, input_buffer)

    def _validate_starting_sequence(self, input_buffer: InputBuffer) -> None:

        if input_buffer.length < constants.STARTING_SEQUENCE_BYTES_LEN:
            return

        starting_sequence_bytes = input_buffer[:constants.STARTING_SEQUENCE_BYTES_LEN]
        if starting_sequence_bytes != constants.STARTING_SEQUENCE_BYTES:
            raise MessageValidationError(
                f"Expected message to begin with starting sequence "
                f"but received first bytes "
                f"'{convert.bytes_to_hex(starting_sequence_bytes)}'"
            )

    def _validate_payload_length(self, msg_type: Optional[bytes], payload_len: Optional[int]) -> None:
        if msg_type is None or payload_len is None:
            return

        if msg_type == BloxrouteMessageType.TRANSACTION:
            size_validation_settings = self._size_validation_settings
            assert size_validation_settings is not None
            if payload_len > size_validation_settings.max_tx_size_bytes:
                raise MessageValidationError(
                    f"Transaction message size exceeds expected max size. "
                    f"Expected: {size_validation_settings.max_tx_size_bytes}. "
                    f"Actual: {payload_len}."
                )

        elif msg_type in {
            BloxrouteMessageType.BROADCAST,
            BloxrouteMessageType.TRANSACTIONS,
            BloxrouteMessageType.TX_SERVICE_SYNC_BLOCKS_SHORT_IDS,
            BloxrouteMessageType.TX_SERVICE_SYNC_TXS,
            BloxrouteMessageType.TRANSACTION_CLEANUP,
            BloxrouteMessageType.BLOCK_CONFIRMATION,
        }:
            size_validation_settings = self._size_validation_settings
            assert size_validation_settings is not None
            if payload_len > size_validation_settings.max_block_size_bytes:
                raise MessageValidationError(
                    f"{msg_type} message size exceeds expected max size. "
                    f"Expected: {size_validation_settings.max_block_size_bytes}. "
                    f"Actual: {payload_len}."
                )

        elif payload_len > constants.DEFAULT_MAX_PAYLOAD_LEN_BYTES:
            raise MessageValidationError(
                f"Message by type '{msg_type}' exceeds expected payload len. "
                f"Expected: {constants.DEFAULT_MAX_PAYLOAD_LEN_BYTES}. "
                f"Actual: {payload_len}."
            )

    def _validate_control_flags(
        self,
        is_full: bool,
        header_len: int,
        payload_len: Optional[int],
        input_buffer: InputBuffer
    ) -> None:
        if not is_full:
            return

        assert payload_len is not None
        if input_buffer.length < header_len + payload_len:
            raise MessageValidationError(
                f"Not enough bytes in the input buffer to get control flags. "
                f"Header length: {header_len}. "
                f"Payload length: {payload_len}. "
                f"Input buffer length: {input_buffer.length}"
            )

        control_flag_byte = input_buffer[header_len + payload_len - 1:header_len + payload_len]
        if BloxrouteMessageControlFlags.VALID not in BloxrouteMessageControlFlags(control_flag_byte[0]):
            raise ControlFlagValidationError(
                f"Control flags byte does not have VALID flag set. Value: {control_flag_byte}.",
                control_flag_byte[0]
            )
