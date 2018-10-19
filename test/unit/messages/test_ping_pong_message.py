from mock import MagicMock

from bxcommon.messages import message, message_types_loader
from bxcommon.messages.ping_message import PingMessage
from bxcommon.messages.pong_message import PongMessage
from bxcommon.test_utils.abstract_test_case import AbstractTestCase


class PingPongMessageTests(AbstractTestCase):
    def setUp(self):
        mock_msg_types = {
            "pong": PongMessage,
            "ping": PingMessage
        }

        message_types_loader.get_message_types = MagicMock(return_value=mock_msg_types)

    def test_ping_message(self):
        self._test_message("ping", message_types_loader.get_message_types()["ping"])

    def test_pong_message(self):
        self._test_message("pong", message_types_loader.get_message_types()["pong"])

    def _test_message(self, msg_type, msg_cls):
        msg = msg_cls()

        self.assertTrue(msg)
        self.assertEqual(msg.msg_type(), msg_type)
        self.assertEqual(msg.payload_len(), 0)

        ping_msg_bytes = msg.rawbytes()
        self.assertTrue(ping_msg_bytes)

        parsed_ping_message = message.parse(ping_msg_bytes)

        self.assertIsInstance(parsed_ping_message, msg_cls)

        self.assertEqual(parsed_ping_message.msg_type(), msg_type)
        self.assertEqual(parsed_ping_message.payload_len(), 0)
