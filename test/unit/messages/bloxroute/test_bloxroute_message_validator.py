from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon import constants
from bxcommon.messages.bloxroute import protocol_version
from bxcommon.messages.bloxroute.bloxroute_message_control_flags import BloxrouteMessageControlFlags
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.bloxroute_message_validator import BloxrouteMessageValidator
from bxcommon.messages.validation.message_validation_error import MessageValidationError
from bxcommon.messages.validation.control_flag_validation_error import ControlFlagValidationError
from bxcommon.messages.validation.message_size_validation_settings import MessageSizeValidationSettings
from bxcommon.test_utils import helpers
from bxcommon.utils.buffers.input_buffer import InputBuffer


class TestBloxrouteMessageValidator(AbstractTestCase):

    def setUp(self) -> None:
        self.message_validation_settings = MessageSizeValidationSettings(max_block_size_bytes=100000,
                                                                         max_tx_size_bytes=50000)
        self.message_validator = BloxrouteMessageValidator(self.message_validation_settings,
                                                           protocol_version.PROTOCOL_VERSION)

    def test_is_valid_starting_sequence__invalid(self):
        message_bytes = bytearray(1000)
        input_buffer = InputBuffer()
        input_buffer.add_bytes(message_bytes)

        self.assertRaises(MessageValidationError, self.message_validator.validate, False,
                          BloxrouteMessageType.TRANSACTION, constants.BX_HDR_COMMON_OFF,
                          self.message_validation_settings.max_tx_size_bytes, input_buffer)

    def test_is_valid_starting_sequence__valid(self):
        message_bytes = bytearray(1000)
        message_bytes[:constants.STARTING_SEQUENCE_BYTES_LEN] = constants.STARTING_SEQUENCE_BYTES
        input_buffer = InputBuffer()
        input_buffer.add_bytes(message_bytes)

        self.message_validator.validate(False, BloxrouteMessageType.TRANSACTION, constants.BX_HDR_COMMON_OFF,
                                        self.message_validation_settings.max_tx_size_bytes, input_buffer)

    def test_is_valid_payload_len(self):
        message_bytes = bytearray(1000)
        message_bytes[:constants.STARTING_SEQUENCE_BYTES_LEN] = constants.STARTING_SEQUENCE_BYTES
        input_buffer = InputBuffer()
        input_buffer.add_bytes(message_bytes)

        # Transaction message tests
        self.assertIsNone(
            self.message_validator.validate(False, BloxrouteMessageType.TRANSACTION, constants.BX_HDR_COMMON_OFF,
                                            self.message_validation_settings.max_tx_size_bytes, input_buffer))
        self.assertIsNone(
            self.message_validator.validate(False, BloxrouteMessageType.TRANSACTION, constants.BX_HDR_COMMON_OFF, 0,
                                            input_buffer))
        self.assertIsNone(
            self.message_validator.validate(False, BloxrouteMessageType.TRANSACTION, constants.BX_HDR_COMMON_OFF,
                                            self.message_validation_settings.max_tx_size_bytes - 1, input_buffer))
        self.assertRaises(MessageValidationError, self.message_validator.validate, False,
                          BloxrouteMessageType.TRANSACTION, constants.BX_HDR_COMMON_OFF,
                          self.message_validation_settings.max_tx_size_bytes + 1, input_buffer)

        # Broadcast message tests
        self.assertIsNone(
            self.message_validator.validate(False, BloxrouteMessageType.BROADCAST, constants.BX_HDR_COMMON_OFF,
                                            self.message_validation_settings.max_block_size_bytes, input_buffer))
        self.assertIsNone(
            self.message_validator.validate(False, BloxrouteMessageType.BROADCAST, constants.BX_HDR_COMMON_OFF, 0,
                                            input_buffer))
        self.assertIsNone(
            self.message_validator.validate(False, BloxrouteMessageType.BROADCAST, constants.BX_HDR_COMMON_OFF,
                                            self.message_validation_settings.max_block_size_bytes - 1, input_buffer))
        self.assertRaises(MessageValidationError, self.message_validator.validate, False,
                          BloxrouteMessageType.BROADCAST, constants.BX_HDR_COMMON_OFF,
                          self.message_validation_settings.max_block_size_bytes + 1, input_buffer)

        # Transactions message
        self.assertIsNone(
            self.message_validator.validate(False, BloxrouteMessageType.TRANSACTIONS, constants.BX_HDR_COMMON_OFF,
                                            self.message_validation_settings.max_block_size_bytes, input_buffer))
        self.assertIsNone(
            self.message_validator.validate(False, BloxrouteMessageType.TRANSACTIONS, constants.BX_HDR_COMMON_OFF, 0,
                                            input_buffer))
        self.assertIsNone(
            self.message_validator.validate(False, BloxrouteMessageType.TRANSACTIONS, constants.BX_HDR_COMMON_OFF,
                                            self.message_validation_settings.max_block_size_bytes - 1, input_buffer))
        self.assertRaises(MessageValidationError, self.message_validator.validate, False,
                          BloxrouteMessageType.TRANSACTIONS, constants.BX_HDR_COMMON_OFF,
                          self.message_validation_settings.max_block_size_bytes + 1, input_buffer)

        # Other types of messages
        self.assertIsNone(
            self.message_validator.validate(False, BloxrouteMessageType.HELLO, constants.BX_HDR_COMMON_OFF,
                                            constants.DEFAULT_MAX_PAYLOAD_LEN_BYTES, input_buffer))
        self.assertIsNone(
            self.message_validator.validate(False, BloxrouteMessageType.HELLO, constants.BX_HDR_COMMON_OFF, 0,
                                            input_buffer))
        self.assertIsNone(
            self.message_validator.validate(False, BloxrouteMessageType.HELLO, constants.BX_HDR_COMMON_OFF,
                                            constants.DEFAULT_MAX_PAYLOAD_LEN_BYTES - 1, input_buffer))
        self.assertRaises(MessageValidationError, self.message_validator.validate, False, BloxrouteMessageType.HELLO,
                          constants.BX_HDR_COMMON_OFF, constants.DEFAULT_MAX_PAYLOAD_LEN_BYTES + 1, input_buffer)

    def test_is_valid_control_flag__invalid(self):
        message_len = 1000
        message_bytes = bytearray(message_len)
        message_bytes[:constants.STARTING_SEQUENCE_BYTES_LEN] = constants.STARTING_SEQUENCE_BYTES
        input_buffer = InputBuffer()
        input_buffer.add_bytes(message_bytes)
        payload_len = message_len - constants.STARTING_SEQUENCE_BYTES_LEN - constants.BX_HDR_COMMON_OFF

        # valid payload len
        self.assertRaises(ControlFlagValidationError, self.message_validator.validate, True,
                          BloxrouteMessageType.TRANSACTION,
                          constants.STARTING_SEQUENCE_BYTES_LEN + constants.BX_HDR_COMMON_OFF, payload_len,
                          input_buffer)

        # invalid payload len - too long
        self.assertRaises(MessageValidationError, self.message_validator.validate, True,
                          BloxrouteMessageType.TRANSACTION,
                          constants.STARTING_SEQUENCE_BYTES_LEN + constants.BX_HDR_COMMON_OFF, message_len,
                          input_buffer)

    def test_is_valid_control_flag__valid(self):
        message_len = 1000
        message_bytes = bytearray(message_len)
        message_bytes[:constants.STARTING_SEQUENCE_BYTES_LEN] = constants.STARTING_SEQUENCE_BYTES
        message_bytes[-1] = BloxrouteMessageControlFlags.VALID
        input_buffer = InputBuffer()
        input_buffer.add_bytes(message_bytes)

        # adding random bytes to the end of intput buffer
        input_buffer.add_bytes(helpers.generate_bytearray(10))

        payload_len = message_len - constants.STARTING_SEQUENCE_BYTES_LEN - constants.BX_HDR_COMMON_OFF

        # valid payload len
        self.message_validator.validate(True, BloxrouteMessageType.TRANSACTION,
                                        constants.STARTING_SEQUENCE_BYTES_LEN + constants.BX_HDR_COMMON_OFF,
                                        payload_len, input_buffer)

        # invalid payload len - too long
        self.assertRaises(MessageValidationError, self.message_validator.validate, True,
                          BloxrouteMessageType.TRANSACTION,
                          constants.STARTING_SEQUENCE_BYTES_LEN + constants.BX_HDR_COMMON_OFF, message_len,
                          input_buffer)
