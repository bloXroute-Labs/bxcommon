from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.messages.bloxroute.bloxroute_message_factory import _BloxrouteMessageFactory
from bxcommon.messages.bloxroute.ping_message import PingMessage
from bxcommon.messages.bloxroute.pong_message import PongMessage
from bxcommon.utils import nonce_generator
import time


class PingPongMessageTests(AbstractTestCase):
    def setUp(self):
        self.message_factory = _BloxrouteMessageFactory()
        self.message_factory._MESSAGE_TYPE_MAPPING = {
            b"pong": PongMessage,
            b"ping": PingMessage
        }

    def test_ping_message(self):
        self._test_message(b"ping", PingMessage, expected_length=PingMessage.KEEP_ALIVE_MESSAGE_LENGTH)

    def test_pong_message(self):
        self._test_message(b"pong", PongMessage, expected_length=PongMessage.PONG_MESSAGE_LENGTH)

    def _test_message(self, msg_type, msg_cls, expected_length):
        msg = msg_cls()

        self.assertTrue(msg)
        self.assertEqual(msg.msg_type(), msg_type)
        self.assertEqual(msg.payload_len(), expected_length)

        ping_msg_bytes = msg.rawbytes()
        self.assertTrue(ping_msg_bytes)

        parsed_ping_message = self.message_factory.create_message_from_buffer(ping_msg_bytes)
        self.assertIsInstance(parsed_ping_message, msg_cls)

        self.assertEqual(parsed_ping_message.msg_type(), msg_type)
        self.assertEqual(parsed_ping_message.payload_len(), expected_length)

    def test_pong_message_timestamp(self):
        t0 = nonce_generator.get_nonce()
        time.sleep(0)
        t1 = nonce_generator.get_nonce()
        msg = PongMessage(t0, t1)
        self.assertEqual(msg.nonce(), t0)
        self.assertEqual(msg.timestamp(), t1)

        new_msg = PongMessage(buf=msg.buf)
        self.assertEqual(msg.nonce(), new_msg.nonce())
