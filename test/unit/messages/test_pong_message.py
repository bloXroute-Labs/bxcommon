from bxcommon.messages.message import Message
from bxcommon.messages.pong_message import PongMessage
from bxcommon.test_utils.abstract_test_case import AbstractTestCase

class PongMessageTests(AbstractTestCase):

    def test_pong_message(self):
        pong_msg = PongMessage()

        self.assertTrue(pong_msg)
        self.assertEqual(pong_msg.msg_type(), 'pong')
        self.assertEqual(pong_msg.payload_len(), 0)

        pong_msg_bytes = pong_msg.rawbytes()
        self.assertTrue(pong_msg_bytes)

        parsed_pong_message = Message.parse(pong_msg_bytes)

        self.assertIsInstance(parsed_pong_message, PongMessage)

        self.assertEqual(parsed_pong_message.msg_type(), 'pong')
        self.assertEqual(parsed_pong_message.payload_len(), 0)




