from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.messages.bloxroute.bloxroute_message_factory import _BloxrouteMessageFactory
from bxcommon.messages.bloxroute.ping_message import PingMessage
from bxcommon.messages.bloxroute.pong_message import PongMessage
from bxcommon.messages.bloxroute.keep_alive_message import KeepAliveMessage


class PingPongMessageTests(AbstractTestCase):
    def setUp(self):
        self.message_factory = _BloxrouteMessageFactory()
        self.message_factory._MESSAGE_TYPE_MAPPING = {
            b"pong": PongMessage,
            b"ping": PingMessage
        }

    def test_ping_message(self):
        self._test_message(b"ping", PingMessage)

    def test_pong_message(self):
        self._test_message(b"pong", PongMessage)

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
