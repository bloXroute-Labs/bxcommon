from bxcommon.messages.bloxroute.bloxroute_message_factory import bloxroute_message_factory
from bxcommon.messages.bloxroute.hello_message import HelloMessage
from bxcommon.messages.bloxroute.v1.bloxroute_message_factory_v1 import bloxroute_message_factory_v1
from bxcommon.messages.bloxroute.v1.hello_message_v1 import HelloMessageV1
from bxcommon.messages.bloxroute.versioning import versioning
from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.utils.buffers.input_buffer import InputBuffer


class VersioningTests(AbstractTestCase):

    def test_is_protocol_supported(self):
        self.assertFalse(0, versioning.is_protocol_supported(1))
        self.assertTrue(1, versioning.is_protocol_supported(1))
        self.assertTrue(1, versioning.is_protocol_supported(2))
        self.assertTrue(1, versioning.is_protocol_supported(3))

    def test_get_message_factory_for_version(self):
        self.assertEqual(bloxroute_message_factory_v1, versioning.get_message_factory_for_version(1))
        self.assertEqual(bloxroute_message_factory, versioning.get_message_factory_for_version(2))
        self.assertRaises(ValueError, versioning.get_message_factory_for_version, 0)
        self.assertRaises(ValueError, versioning.get_message_factory_for_version, 3)

    def test_get_connection_protocol_version__v1(self):
        hello_msg_v1 = HelloMessageV1(idx=0)
        input_buffer = InputBuffer()
        input_buffer.add_bytes(hello_msg_v1.rawbytes())

        self.assertEqual(1, versioning.get_connection_protocol_version(input_buffer))

    def test_get_connection_protocol_version__over_v2(self):
        self._test_version_over_v1(2)
        self._test_version_over_v1(3)
        self._test_version_over_v1(4)

    def _test_version_over_v1(self, version):
        hello_msg = HelloMessage(protocol_version=version, idx=0, network_num=1)
        input_buffer = InputBuffer()
        input_buffer.add_bytes(hello_msg.rawbytes())

        self.assertEqual(version, versioning.get_connection_protocol_version(input_buffer))
