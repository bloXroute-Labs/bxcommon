from bxcommon.test_utils.mocks.mock_message import MockMessage
from bxcommon.messages.message import Message, parse, peek_message
from bxcommon.utils.buffers.input_buffer import InputBuffer
from bxcommon.constants import HDR_COMMON_OFF
from bxcommon.exceptions import UnrecognizedCommandError, PayloadLenError
from mock import MagicMock
from bxcommon.messages import message_types_loader
from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.messages.ack_message import AckMessage
from bxcommon.messages.broadcast_message import BroadcastMessage
from bxcommon.messages.hello_message import HelloMessage
from bxcommon.messages.ping_message import PingMessage
from bxcommon.messages.pong_message import PongMessage
from bxcommon.messages.tx_assign_message import TxAssignMessage
from bxcommon.messages.tx_message import TxMessage
from bxcommon.messages.get_txs_message import GetTxsMessage
from bxcommon.messages.txs_message import TxsMessage


class MessageTest(AbstractTestCase):

    def setUp(self):
        self.buf1 = bytearray([i for i in range(40)])
        self.payload_len1 = 20
        self.msg_type1 = "example"
        self.message1 = Message(msg_type=self.msg_type1, payload_len=self.payload_len1, buf=self.buf1)
        self.buf2 = bytearray([i for i in range(20)])
        self.payload_len2 = 50
        self.msg_type2 = "hello"
        self.message2 = Message(msg_type=self.msg_type2, payload_len=self.payload_len2, buf=self.buf2)

    def test_init(self):

        with self.assertRaises(ValueError):
            Message(msg_type=None, payload_len=20, buf=bytearray([i for i in range(40)]))
        with self.assertRaises(ValueError):
            Message(msg_type="hello", payload_len=-5, buf=bytearray([i for i in range(40)]))
        with self.assertRaises(ValueError):
            Message(msg_type="hello", payload_len=20, buf=bytearray([i for i in range(10)]))

        self.assertEqual(self.buf1, self.message1.buf)
        self.assertEqual(self.buf1, self.message1._memoryview)
        self.assertEqual(self.msg_type1, self.message1._msg_type)
        self.assertIsNone(self.message1._payload)
        self.assertEqual(self.payload_len1, self.message1._payload_len)

    def test_rawbytes(self):
        self.assertIsInstance(self.message1.rawbytes(), memoryview)
        self.assertEqual(20, self.message1._payload_len)
        message2_rawbytes = self.message2.rawbytes()
        self.assertEqual(50, self.message2._payload_len)
        self.assertEqual(message2_rawbytes, memoryview(self.message2._memoryview))

    def test_peek_message(self):
        in_buf = InputBuffer()
        self.assertEqual((False, None, None), peek_message(in_buf))
        in_buf.add_bytes(self.message1.rawbytes())
        self.assertEqual((True, self.msg_type1, self.payload_len1), peek_message(in_buf))

        in_buf1 = InputBuffer()
        in_buf1.add_bytes(self.message2.rawbytes())
        self.assertEqual((False, self.msg_type2, self.payload_len2), peek_message(in_buf1))

    def test_parse(self):
        with self.assertRaises(UnrecognizedCommandError):
            parse(self.message1.rawbytes())

        mock_msg_types = {
            'hello': HelloMessage,
            'ack': AckMessage,
            'ping': PingMessage,
            'pong': PongMessage,
            'broadcast': BroadcastMessage,
            'tx': TxMessage,
            'txassign': TxAssignMessage,
            'gettxs': GetTxsMessage,
            'txs': TxsMessage,
            'example': MockMessage
        }

        message_types_loader.get_message_types = MagicMock(return_value=mock_msg_types)

        mock_message1 = MockMessage(buf=self.buf1, payload_len=40, msg_type='example')

        with self.assertRaises(PayloadLenError):
            parse(mock_message1.rawbytes())

        mock_message2 = MockMessage(buf=self.buf1, payload_len=len(self.buf1) - HDR_COMMON_OFF, msg_type='example')
        mock_message2_bytes = parse(mock_message2.rawbytes())

        self.assertEqual(mock_message2._payload_len, mock_message2_bytes._payload_len)
        self.assertEqual(mock_message2.buf, mock_message2_bytes.buf)
        self.assertEqual(mock_message2._msg_type, mock_message2_bytes._msg_type)

        mock_message3 = MockMessage(buf=self.buf2, payload_len=4, msg_type='example')
        mock_message3_bytes = parse(mock_message3.rawbytes())
        self.assertNotEqual(mock_message2.buf, mock_message3_bytes.buf)

    def test_msg_type(self):
        self.assertEqual(self.msg_type1, self.message1.msg_type())

    def test_payload_len(self):
        self.assertEqual(self.payload_len1, self.message1.payload_len())

    def test_payload(self):
        self.assertIsNone(self.message1._payload)
        self.assertEqual(self.buf1[HDR_COMMON_OFF:self.payload_len1 + HDR_COMMON_OFF], self.message1.payload())
        self.assertEqual(self.buf1[HDR_COMMON_OFF:self.payload_len1 + HDR_COMMON_OFF], self.message1._payload)

