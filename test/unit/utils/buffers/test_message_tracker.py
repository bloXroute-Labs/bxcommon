from bxcommon.messages.bloxroute.tx_message import TxMessage
from bxcommon.test_utils import helpers
from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.test_utils.mocks.mock_connection import MockConnection
from bxcommon.test_utils.mocks.mock_node import MockNode
from bxcommon.test_utils.mocks.mock_socket_connection import (
    MockSocketConnection,
)
from bxcommon.utils.buffers.message_tracker import MessageTracker
from bxcommon.utils.buffers.output_buffer import OutputBuffer


class MessageTrackerTest(AbstractTestCase):
    def setUp(self) -> None:
        self.node = MockNode(
            helpers.get_common_opts(1001, external_ip="128.128.128.128")
        )
        self.tracker = MessageTracker(
            MockConnection(MockSocketConnection(1, self.node), self.node)
        )
        self.output_buffer = OutputBuffer(enable_buffering=True)

    def test_empty_bytes_no_bytes_sent(self):
        message = TxMessage(
            helpers.generate_object_hash(),
            5,
            tx_val=helpers.generate_bytearray(250),
        )
        message_length = len(message.rawbytes())
        self.output_buffer.enqueue_msgbytes(message.rawbytes())
        self.output_buffer.flush()
        self.tracker.append_message(message_length, message)

        self.output_buffer.safe_empty()
        self.tracker.empty_bytes(self.output_buffer.length)

        self.assertEqual(0, self.output_buffer.length)
        self.assertEqual(0, self.tracker.bytes_remaining)
        self.assertEqual(0, len(self.tracker.messages))

    def test_empty_bytes(self):
        message1 = TxMessage(
            helpers.generate_object_hash(),
            5,
            tx_val=helpers.generate_bytearray(250),
        )
        message2 = TxMessage(
            helpers.generate_object_hash(),
            5,
            tx_val=helpers.generate_bytearray(250),
        )
        message3 = TxMessage(
            helpers.generate_object_hash(),
            5,
            tx_val=helpers.generate_bytearray(250),
        )
        message_length = len(message1.rawbytes())

        self.output_buffer.enqueue_msgbytes(message1.rawbytes())
        self.output_buffer.flush()
        self.output_buffer.enqueue_msgbytes(message2.rawbytes())
        self.output_buffer.enqueue_msgbytes(message3.rawbytes())

        self.tracker.append_message(message_length, message1)
        self.tracker.append_message(message_length, message2)
        self.tracker.append_message(message_length, message3)

        self.output_buffer.advance_buffer(120)
        self.tracker.advance_bytes(120)

        self.output_buffer.safe_empty()
        self.assertEqual(message_length - 120, self.output_buffer.length)

        self.tracker.empty_bytes(self.output_buffer.length)

        self.assertEqual(1, len(self.tracker.messages))
        self.assertEqual(message_length - 120, self.tracker.bytes_remaining)
        self.assertEqual(120, self.tracker.messages[0].sent_bytes)

    def test_empty_bytes_more_bytes(self):
        total_bytes = 0
        for _ in range(100):
            message = TxMessage(
                helpers.generate_object_hash(),
                5,
                tx_val=helpers.generate_bytearray(2500),
            )
            message_length = len(message.rawbytes())
            total_bytes += message_length
            self.output_buffer.enqueue_msgbytes(message.rawbytes())
            self.tracker.append_message(message_length, message)

        self.output_buffer.advance_buffer(3500)
        self.tracker.advance_bytes(3500)

        self.output_buffer.safe_empty()
        self.tracker.empty_bytes(self.output_buffer.length)

        self.assertEqual(
            self.output_buffer.length, self.tracker.bytes_remaining
        )
