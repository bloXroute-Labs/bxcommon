from mock import MagicMock

from bxcommon.messages.abstract_message import AbstractMessage
from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon import constants
from bxcommon.connections.abstract_connection import AbstractConnection
from bxcommon.connections.connection_state import ConnectionState
from bxcommon.constants import BLOXROUTE_HELLO_MESSAGES
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.messages.bloxroute.ack_message import AckMessage
from bxcommon.messages.bloxroute.bloxroute_message_factory import bloxroute_message_factory, _BloxrouteMessageFactory
from bxcommon.messages.bloxroute.hello_message import HelloMessage
from bxcommon.messages.bloxroute.ping_message import PingMessage
from bxcommon.messages.bloxroute.pong_message import PongMessage
from bxcommon.test_utils.helpers import create_connection


class AbstractConnectionTest(AbstractTestCase):
    class TestMessageFactory(_BloxrouteMessageFactory):
        def get_message_type_mapping(self):
            return {
                b"hello": HelloMessage,
                b"pong": PongMessage
            }

    class TestAbstractConnection(AbstractConnection):
        def __init__(self, *args, **kwargs):
            super(AbstractConnectionTest.TestAbstractConnection, self).__init__(*args, **kwargs)
            self.hello_messages = BLOXROUTE_HELLO_MESSAGES
            self.header_size = constants.STARTING_SEQUENCE_BYTES_LEN + constants.BX_HDR_COMMON_OFF
            self.message_factory = AbstractConnectionTest.TestMessageFactory()
            self.pong_message = PongMessage()
            self.ack_message = AckMessage()

        def ping_message(self) -> AbstractMessage:
            return PingMessage()

    def setUp(self):
        self.connection = create_connection(self.TestAbstractConnection)

    def test_process_message_incomplete_message_aborts(self):
        self.connection.inputbuf.add_bytes(PongMessage().rawbytes()[:-2])
        self.connection.pop_next_message = MagicMock(wraps=self.connection)

        self.connection.process_message()
        self.connection.pop_next_message.assert_not_called()

    def test_process_message_quit_on_bad_message(self):
        bad_message = AbstractBloxrouteMessage(
            b"badtype",
            0,
            bytearray(
                constants.STARTING_SEQUENCE_BYTES_LEN
                + constants.BX_HDR_COMMON_OFF
                + constants.CONTROL_FLAGS_LEN
            )
        ).rawbytes()
        self.connection.inputbuf.add_bytes(bad_message)
        self.connection.inputbuf.add_bytes(bad_message)
        self.connection.inputbuf.add_bytes(bad_message)
        self.connection.inputbuf.add_bytes(bad_message)

        self.connection.process_message()
        self.assertFalse(self.connection.is_alive())

    def test_process_message_not_yet_setup(self):
        self.connection.inputbuf.add_bytes(PongMessage().rawbytes())
        self.connection.msg_pong = MagicMock()

        self.connection.process_message()
        self.connection.msg_pong.assert_not_called()
        self.assertFalse(self.connection.is_alive())

    def test_process_message_handler(self):
        mock_pong = MagicMock()
        self.connection.message_handlers = {
            b"hello": self.connection.msg_hello,
            b"pong": mock_pong
        }
        self.connection.on_connection_established()
        self.connection.inputbuf.add_bytes(HelloMessage(protocol_version=1, network_num=2).rawbytes())
        self.connection.inputbuf.add_bytes(PongMessage().rawbytes())

        self.connection.process_message()
        mock_pong.assert_called_once()

    def test_process_message_handler_abort_in_between_messages(self):
        mock_pong = MagicMock()
        self.connection.message_handlers = {
            b"hello": self.connection.msg_hello,
            b"ack": lambda _msg: self.connection.mark_for_close(),
            b"pong": mock_pong
        }
        self.connection.on_connection_established()
        self.connection.inputbuf.add_bytes(HelloMessage(protocol_version=1, network_num=2).rawbytes())
        self.connection.inputbuf.add_bytes(AckMessage().rawbytes())
        self.connection.inputbuf.add_bytes(PongMessage().rawbytes())

        self.connection.process_message()
        mock_pong.assert_not_called()

    def test_msg_ping(self):
        self.connection.msg_ping(PingMessage())
        self.assertTrue(self.connection.outputbuf.length > 0)
        self.connection.outputbuf.flush()

        output_buf_msg = self.connection.outputbuf.get_buffer()
        pong_reply_msg = bloxroute_message_factory.create_message_from_buffer(output_buf_msg)

        self.assertTrue(pong_reply_msg)
        self.assertTrue(isinstance(pong_reply_msg, PongMessage))

    def test_msg_pong(self):
        self.connection.msg_pong(PongMessage())
        self.assertTrue(self.connection.outputbuf.length == 0)

    def test_ping_pong_cant_send_pings(self):
        self.connection.enqueue_msg = MagicMock()
        self.connection.can_send_pings = False

        self.connection.schedule_pings()
        self.assertIsNone(self.connection.ping_alarm_id)

        result = self.connection.send_ping()
        self.connection.enqueue_msg.assert_not_called()
        self.assertEqual(constants.CANCEL_ALARMS, result)

    def test_ping_pong_send_pings(self):
        self.connection.enqueue_msg = MagicMock()
        self.connection.can_send_pings = True

        self.connection.schedule_pings()
        self.assertIsNotNone(self.connection.ping_alarm_id)

        result = self.connection.send_ping()
        self.connection.enqueue_msg.assert_called_once_with(PingMessage())
        self.assertEqual(self.connection.ping_interval_s, result)
