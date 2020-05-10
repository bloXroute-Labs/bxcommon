from abc import ABCMeta, abstractmethod

from bxcommon.test_utils import helpers
from bxcommon.test_utils.abstract_test_case import AbstractTestCase


class MessageFactoryTestCase(AbstractTestCase):
    __meta__ = ABCMeta

    @abstractmethod
    def get_message_factory(self):
        pass

    def get_message_preview_successfully(self, message, expected_command, expected_payload_length):
        (
            is_full_message, command, payload_length
        ) = self.get_message_factory().get_message_header_preview_from_input_buffer(
            helpers.create_input_buffer_with_message(message)
        )
        self.assertTrue(is_full_message)
        self.assertEqual(expected_command, command)
        self.assertEqual(expected_payload_length, payload_length)

    def create_message_successfully(self, message, message_type):
        result = self.get_message_factory().create_message_from_buffer(bytearray(message.rawbytes().tobytes()))
        self.assertIsInstance(result, message_type)
        return result
