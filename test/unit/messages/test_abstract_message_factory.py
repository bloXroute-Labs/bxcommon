import struct

from bxcommon.constants import HDR_COMMON_OFF, MSG_NULL_BYTE
from bxcommon.exceptions import ParseError, UnrecognizedCommandError
from bxcommon.messages.abstract_message_factory import AbstractMessageFactory
from bxcommon.messages.bloxroute.message import Message
from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.utils.buffers.input_buffer import InputBuffer


def create_input_buffer_with_bytes(contents):
    input_buffer = InputBuffer()
    input_buffer.add_bytes(contents)
    return input_buffer


class AbstractMessageFactoryTest(AbstractTestCase):
    PAYLOAD_LENGTH = 8
    TOTAL_LENGTH = PAYLOAD_LENGTH + HDR_COMMON_OFF

    class TestMessage(Message):
        HEADER_LENGTH = HDR_COMMON_OFF

        def __init__(self, message_type=b"test", buf=None):
            self.initialized = False
            if buf is None:
                buf = bytearray(AbstractMessageFactoryTest.PAYLOAD_LENGTH + HDR_COMMON_OFF)
            super(AbstractMessageFactoryTest.TestMessage, self).__init__(message_type,
                                                                         AbstractMessageFactoryTest.PAYLOAD_LENGTH,
                                                                         buf)

        @classmethod
        def unpack(cls, buf):
            command, payload_length = struct.unpack_from("<12sL", buf)
            return command.rstrip(MSG_NULL_BYTE), payload_length

        @classmethod
        def validate_payload(cls, buf, unpacked_args):
            if all(i == 12 for i in buf[HDR_COMMON_OFF:]):
                raise ValueError("test failure")

        @classmethod
        def initialize_class(cls, cls_type, buf, unpacked_args):
            instance = cls_type(buf=buf)
            instance.initialized = True
            return instance

    class TestMessageFactory(AbstractMessageFactory):
        def __init__(self):
            super(AbstractMessageFactoryTest.TestMessageFactory, self).__init__()
            self.base_message_type = AbstractMessageFactoryTest.TestMessage
            self.message_type_mapping = {
                b"test": AbstractMessageFactoryTest.TestMessage
            }

    def setUp(self):
        self.sut = self.TestMessageFactory()

    def test_get_message_header_preview_too_short(self):
        input_buffer = create_input_buffer_with_bytes(bytearray(1))

        is_full_message, command, payload_length = self.sut.get_message_header_preview_from_input_buffer(input_buffer)
        self.assertFalse(is_full_message)
        self.assertIsNone(command)
        self.assertIsNone(payload_length)

    def test_get_message_header_preview_message(self):
        input_buffer = create_input_buffer_with_bytes(self.TestMessage().rawbytes())

        is_full_message, command, payload_length = self.sut.get_message_header_preview_from_input_buffer(input_buffer)
        self.assertTrue(is_full_message)
        self.assertEquals(b"test", command)
        self.assertEquals(self.PAYLOAD_LENGTH, payload_length)

    def test_create_message_too_short(self):
        with self.assertRaises(ParseError):
            self.sut.create_message_from_buffer(bytearray(1))

    def test_create_message_unrecognized_message_type(self):
        with self.assertRaises(UnrecognizedCommandError):
            self.sut.create_message_from_buffer(
                AbstractMessageFactoryTest.TestMessage(b"fake", bytearray(self.TOTAL_LENGTH)).rawbytes())

    def test_create_message_validation_failed(self):
        invalid_bytes = bytearray(12 for _ in range(self.TOTAL_LENGTH))
        with self.assertRaises(ValueError):
            self.sut.create_message_from_buffer(self.TestMessage(buf=invalid_bytes).rawbytes())

    def test_create_message_initialized_test_message(self):
        valid_bytes = bytearray(0 for _ in range(self.TOTAL_LENGTH))
        message = self.sut.create_message_from_buffer(self.TestMessage(buf=valid_bytes).rawbytes())
        self.assertIsInstance(message, AbstractMessageFactoryTest.TestMessage)
        self.assertTrue(message.initialized)
