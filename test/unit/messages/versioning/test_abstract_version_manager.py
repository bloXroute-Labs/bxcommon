from bxcommon.constants import VERSIONED_HELLO_MSG_MIN_PAYLOAD_LEN
from bxcommon.messages.abstract_message_factory import AbstractMessageFactory
from bxcommon.messages.bloxroute.broadcast_message import BroadcastMessage
from bxcommon.messages.bloxroute.hello_message import HelloMessage
from bxcommon.messages.bloxroute.v1.hello_message_v1 import HelloMessageV1
from bxcommon.messages.versioning.abstract_version_manager import AbstractVersionManager
from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.utils import crypto
from bxcommon.utils.buffers.input_buffer import InputBuffer
from bxcommon.utils.object_hash import ObjectHash


class MessageFactory(AbstractMessageFactory):
    pass


class MessageFactoryV1(AbstractMessageFactory):
    pass


message_factory = MessageFactory()
message_factory_v1 = MessageFactoryV1()


class VersionManager(AbstractVersionManager):
    CURRENT_PROTOCOL_VERSION = 2
    VERSION_MESSAGE_MAIN_LENGTH = VERSIONED_HELLO_MSG_MIN_PAYLOAD_LEN

    def __init__(self):
        super(VersionManager, self).__init__()
        self.protocol_to_factory_mapping = {
            1: message_factory_v1,
            2: message_factory
        }
        self.protocol_to_converter_factory_mapping = {}
        self.version_message_command = "hello"


class AbstractVersionManagerTest(AbstractTestCase):

    def setUp(self):
        self.version_manager = VersionManager()

    def test_is_protocol_supported(self):
        self.assertFalse(self.version_manager.is_protocol_supported(0))
        self.assertTrue(self.version_manager.is_protocol_supported(1))
        self.assertTrue(self.version_manager.is_protocol_supported(2))
        self.assertTrue(self.version_manager.is_protocol_supported(3))

    def test_get_message_factory_for_version(self):
        self.assertEqual(message_factory_v1, self.version_manager.get_message_factory_for_version(1))
        self.assertEqual(message_factory, self.version_manager.get_message_factory_for_version(2))
        with self.assertRaises(ValueError):
            self.version_manager.get_message_factory_for_version(0)
        with self.assertRaises(NotImplementedError):
            self.version_manager.get_message_factory_for_version(3)

    def test_get_connection_protocol_version__wrong_message(self):
        wrong_message = BroadcastMessage(
            msg_hash=ObjectHash(crypto.double_sha256("hello")),
            network_num=1,
            blob=bytearray(1))
        input_buffer = InputBuffer()
        input_buffer.add_bytes(wrong_message.rawbytes())

        self.assertEqual(0, self.version_manager.get_connection_protocol_version(input_buffer))

    def test_get_connection_protocol_version__v1(self):
        hello_msg_v1 = HelloMessageV1(idx=0)
        input_buffer = InputBuffer()
        input_buffer.add_bytes(hello_msg_v1.rawbytes())

        self.assertEqual(1, self.version_manager.get_connection_protocol_version(input_buffer))

    def test_get_connection_protocol_version__over_v2(self):
        self._test_version_over_v1(2)
        self._test_version_over_v1(3)
        self._test_version_over_v1(4)

    def _test_version_over_v1(self, version):
        hello_msg = HelloMessage(protocol_version=version, network_num=1)
        input_buffer = InputBuffer()
        input_buffer.add_bytes(hello_msg.rawbytes())

        self.assertEqual(version, self.version_manager.get_connection_protocol_version(input_buffer))
