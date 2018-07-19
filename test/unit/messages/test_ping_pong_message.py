from bxcommon.messages.message import Message
from bxcommon.messages.ping_message import PingMessage
from bxcommon.messages.pong_message import PongMessage
from bxcommon.test_utils.abstract_test_case import AbstractTestCase


class PingPongMessageTests(AbstractTestCase):

    def test_ping_message(self):
        self._test_message("ping", PingMessage)

    def test_pong_message(self):
        self._test_message("pong", PongMessage)

    def _test_message(self, msg_type, msg_cls):
        msg = msg_cls()

        self.assertTrue(msg)
        self.assertEqual(msg.msg_type(), msg_type)
        self.assertEqual(msg.payload_len(), 0)

        ping_msg_bytes = msg.rawbytes()
        self.assertTrue(ping_msg_bytes)

        parsed_ping_message = Message.parse(ping_msg_bytes)

        self.assertIsInstance(parsed_ping_message, msg_cls)

        self.assertEqual(parsed_ping_message.msg_type(), msg_type)
        self.assertEqual(parsed_ping_message.payload_len(), 0)
