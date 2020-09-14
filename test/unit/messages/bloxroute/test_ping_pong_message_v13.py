from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.messages.bloxroute.ping_message import PingMessage
from bxcommon.messages.bloxroute.v13.pong_message_v13 import PongMessageV13
from bxcommon.messages.bloxroute.keep_alive_message import KeepAliveMessage
from bxcommon.messages.bloxroute.v13.bloxroute_message_factory_v13 import bloxroute_message_factory_v13


class PingPongMessageTests(AbstractTestCase):
    def setUp(self):
        self.message_factory = bloxroute_message_factory_v13
        self.message_factory._MESSAGE_TYPE_MAPPING = {
            b"pong": PongMessageV13,
            b"ping": PingMessage
        }

    def test_ping_message(self):
        self._test_message(b"ping", PingMessage)

    def test_pong_message(self):
        self._test_message(b"pong", PongMessageV13)

    def _test_message(self, msg_type, msg_cls):
        msg = msg_cls()

        self.assertTrue(msg)
        self.assertEqual(msg.msg_type(), msg_type)
        self.assertEqual(msg.payload_len(), KeepAliveMessage.KEEP_ALIVE_MESSAGE_LENGTH)

        ping_msg_bytes = msg.rawbytes()
        self.assertTrue(ping_msg_bytes)

        parsed_ping_message = self.message_factory.create_message_from_buffer(ping_msg_bytes)

        self.assertIsInstance(parsed_ping_message, msg_cls)

        self.assertEqual(parsed_ping_message.msg_type(), msg_type)
        self.assertEqual(parsed_ping_message.payload_len(), KeepAliveMessage.KEEP_ALIVE_MESSAGE_LENGTH)
