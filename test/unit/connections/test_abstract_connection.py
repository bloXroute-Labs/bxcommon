from mock import MagicMock

from bxcommon.connections.abstract_connection import AbstractConnection
from bxcommon.messages import message, message_types_loader
from bxcommon.messages.ping_message import PingMessage
from bxcommon.messages.pong_message import PongMessage
from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.test_utils.helpers import create_connection


class AbstractConnectionTest(AbstractTestCase):

    def setUp(self):
        self.connection = create_connection(AbstractConnection)
        mock_msg_types = {
            "pong": PongMessage
        }

        message_types_loader.get_message_types = MagicMock(return_value=mock_msg_types)

    def test_msg_ping(self):
        self.connection.msg_ping(PingMessage())
        self.assertTrue(self.connection.outputbuf.length > 0)

        output_buf_msg = self.connection.outputbuf.get_buffer()
        pong_reply_msg = message.parse(output_buf_msg)

        self.assertTrue(pong_reply_msg)
        self.assertTrue(isinstance(pong_reply_msg, PongMessage))

    def test_msg_pong(self):
        self.connection.msg_pong(PongMessage())
        self.assertTrue(self.connection.outputbuf.length == 0)
