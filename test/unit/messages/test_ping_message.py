from bxcommon.messages.message import Message
from bxcommon.messages.ping_message import PingMessage
from bxcommon.test_utils.abstract_test_case import AbstractTestCase

class PingMessageTests(AbstractTestCase):

    def test_ping_message(self):
        ping_msg = PingMessage()

        self.assertTrue(ping_msg)
        self.assertEqual(ping_msg.msg_type(), 'ping')
        self.assertEqual(ping_msg.payload_len(), 0)

        ping_msg_bytes = ping_msg.rawbytes()
        self.assertTrue(ping_msg_bytes)

        parsed_ping_message = Message.parse(ping_msg_bytes)

        self.assertIsInstance(parsed_ping_message, PingMessage)

        self.assertEqual(parsed_ping_message.msg_type(), 'ping')
        self.assertEqual(parsed_ping_message.payload_len(), 0)




