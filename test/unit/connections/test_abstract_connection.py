from mock import MagicMock

from bxcommon.connections.abstract_connection import AbstractConnection
from bxcommon.connections.connection_state import ConnectionState
from bxcommon.constants import BLOXROUTE_HELLO_MESSAGES, HDR_COMMON_OFF
from bxcommon.messages.bloxroute.ack_message import AckMessage
from bxcommon.messages.bloxroute.bloxroute_message_factory import bloxroute_message_factory, _BloxrouteMessageFactory
from bxcommon.messages.bloxroute.hello_message import HelloMessage
from bxcommon.messages.bloxroute.message import Message
from bxcommon.messages.bloxroute.ping_message import PingMessage
from bxcommon.messages.bloxroute.pong_message import PongMessage
from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.test_utils.helpers import create_connection


class AbstractConnectionTest(AbstractTestCase):
    class TestMessageFactory(_BloxrouteMessageFactory):
        def get_message_type_mapping(self):
            return {
                "hello": HelloMessage,
                "pong": PongMessage
            }

    class TestAbstractConnection(AbstractConnection):
        def __init__(self, *args, **kwargs):
            super(AbstractConnectionTest.TestAbstractConnection, self).__init__(*args, **kwargs)
            self.hello_messages = BLOXROUTE_HELLO_MESSAGES
            self.header_size = HDR_COMMON_OFF
            self.message_factory = AbstractConnectionTest.TestMessageFactory()
            self.ping_message = PingMessage()
            self.pong_message = PongMessage()
            self.ack_message = AckMessage()

    def setUp(self):
        self.connection = create_connection(self.TestAbstractConnection)

    def test_process_message_incomplete_message_aborts(self):
        self.connection.inputbuf.add_bytes(PongMessage().rawbytes()[:-2])
        self.connection.pop_next_message = MagicMock(wraps=self.connection)

        self.connection.process_message()
        self.connection.pop_next_message.assert_not_called()

    def test_process_message_quit_on_bad_message(self):
        bad_message = Message("badtype", 0, bytearray(HDR_COMMON_OFF)).rawbytes()
        self.connection.inputbuf.add_bytes(bad_message)
        self.connection.inputbuf.add_bytes(bad_message)
        self.connection.inputbuf.add_bytes(bad_message)
        self.connection.inputbuf.add_bytes(bad_message)

        self.connection.process_message()
        self.assertTrue(self.connection.state & ConnectionState.MARK_FOR_CLOSE)

    def test_process_message_not_yet_setup(self):
        self.connection.inputbuf.add_bytes(PongMessage().rawbytes())
        self.connection.msg_pong = MagicMock()

        self.connection.process_message()
        self.connection.msg_pong.assert_not_called()

    def test_process_message_handler_(self):
        mock_pong = MagicMock()
        self.connection.message_handlers = {
            "hello": self.connection.msg_hello,
            "pong": mock_pong
        }
        self.connection.inputbuf.add_bytes(HelloMessage(1, 2, 3).rawbytes())
        self.connection.inputbuf.add_bytes(PongMessage().rawbytes())

        self.connection.process_message()
        mock_pong.assert_called_once()

    def test_msg_ping(self):
        self.connection.msg_ping(PingMessage())
        self.assertTrue(self.connection.outputbuf.length > 0)
        self.connection.outputbuf._flush_to_buffer()

        output_buf_msg = self.connection.outputbuf.get_buffer()
        pong_reply_msg = bloxroute_message_factory.create_message_from_buffer(output_buf_msg)

        self.assertTrue(pong_reply_msg)
        self.assertTrue(isinstance(pong_reply_msg, PongMessage))

    def test_msg_pong(self):
        self.connection.msg_pong(PongMessage())
        self.assertTrue(self.connection.outputbuf.length == 0)
