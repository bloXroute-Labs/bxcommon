import time
import unittest
from collections import deque

from mock import MagicMock

from bxcommon.constants import OUTPUT_BUFFER_BATCH_MAX_HOLD_TIME, OUTPUT_BUFFER_MIN_SIZE
from bxcommon.test_utils import helpers
from bxcommon.utils.buffers.output_buffer import OutputBuffer


class TestOutputBuffer(unittest.TestCase):
    def setUp(self):
        self.output_buffer = OutputBuffer(enable_buffering=True)

    def test_get_buffer(self):
        self.assertEqual(OutputBuffer.EMPTY, self.output_buffer.get_buffer())

        data1 = bytearray([i for i in range(20)])
        self.output_buffer.enqueue_msgbytes(data1)
        self.output_buffer.flush()
        self.assertEqual(data1, self.output_buffer.get_buffer())

        data2 = bytearray([i for i in range(20, 40)])
        self.output_buffer.enqueue_msgbytes(data2)
        self.output_buffer.flush()
        self.assertEqual(data1, self.output_buffer.get_buffer())

        new_index = 10
        self.output_buffer.index = new_index
        self.assertEqual(data1[new_index:], self.output_buffer.get_buffer())

    def test_advance_buffer(self):
        with self.assertRaises(ValueError):
            self.output_buffer.advance_buffer(5)

        data1 = bytearray([i for i in range(20)])
        self.output_buffer.enqueue_msgbytes(data1)
        self.output_buffer.flush()
        data2 = bytearray([i for i in range(20, 40)])
        self.output_buffer.enqueue_msgbytes(data2)
        self.output_buffer.flush()

        self.output_buffer.advance_buffer(10)
        self.assertEqual(10, self.output_buffer.index)
        self.assertEqual(30, self.output_buffer.length)

        self.output_buffer.advance_buffer(10)
        self.assertEqual(0, self.output_buffer.index)
        self.assertEqual(1, len(self.output_buffer.output_msgs))

    def test_at_msg_boundary(self):
        self.assertTrue(self.output_buffer.at_msg_boundary())
        self.output_buffer.index = 1
        self.assertFalse(self.output_buffer.at_msg_boundary())

    def test_enqueue_msgbytes(self):
        with self.assertRaises(ValueError):
            self.output_buffer.enqueue_msgbytes("f")

        data1 = bytearray([i for i in range(20)])
        self.output_buffer.enqueue_msgbytes(data1)
        self.output_buffer.flush()
        self.assertEqual(data1, self.output_buffer.get_buffer())

        data2 = bytearray([i for i in range(20, 40)])
        self.output_buffer.enqueue_msgbytes(data2)
        self.output_buffer.flush()
        self.assertEqual(data1, self.output_buffer.get_buffer())

        new_index = 10
        self.output_buffer.index = new_index
        self.assertEqual(data1[new_index:], self.output_buffer.get_buffer())

    def test_prepend_msgbytes(self):
        with self.assertRaises(ValueError):
            self.output_buffer.prepend_msgbytes("f")

        data1 = bytearray([i for i in range(20)])
        self.output_buffer.prepend_msgbytes(data1)

        data2 = bytearray([i for i in range(20, 40)])
        self.output_buffer.prepend_msgbytes(data2)

        confirm1 = deque()
        confirm1.append(data2)
        confirm1.append(data1)

        self.assertEqual(confirm1, self.output_buffer.output_msgs)
        self.assertEqual(40, self.output_buffer.length)

        self.output_buffer.advance_buffer(10)

        data3 = bytearray([i for i in range(40, 60)])
        self.output_buffer.prepend_msgbytes(data3)

        confirm2 = deque()
        confirm2.append(data2)
        confirm2.append(data3)
        confirm2.append(data1)

        self.assertEqual(confirm2, self.output_buffer.output_msgs)
        self.assertEqual(50, self.output_buffer.length)

    def test_has_more_bytes(self):
        self.assertFalse(self.output_buffer.has_more_bytes())
        self.output_buffer.length = 1
        self.assertTrue(self.output_buffer.has_more_bytes())

    def test_flush_get_buffer_on_time(self):
        data1 = bytearray(i for i in range(20))
        self.output_buffer.enqueue_msgbytes(data1)
        self.assertEqual(OutputBuffer.EMPTY, self.output_buffer.get_buffer())

        time.time = MagicMock(return_value=time.time() + OUTPUT_BUFFER_BATCH_MAX_HOLD_TIME + 0.001)
        self.assertEqual(data1, self.output_buffer.get_buffer())

    def test_flush_get_buffer_on_size(self):
        data1 = bytearray(i for i in range(20))
        self.output_buffer.enqueue_msgbytes(data1)
        self.assertEqual(OutputBuffer.EMPTY, self.output_buffer.get_buffer())

        data2 = bytearray(1 for _ in range(OUTPUT_BUFFER_MIN_SIZE))
        self.output_buffer.enqueue_msgbytes(data2)
        self.assertNotEqual(OutputBuffer.EMPTY, self.output_buffer.get_buffer())

    def test_safe_empty(self):
        self.output_buffer = OutputBuffer(enable_buffering=False)
        messages = [
            helpers.generate_bytearray(10),
            helpers.generate_bytearray(10)
        ]
        for message in messages:
            self.output_buffer.enqueue_msgbytes(message)

        self.output_buffer.advance_buffer(5)
        self.assertEqual(15, len(self.output_buffer))

        self.output_buffer.safe_empty()
        self.assertEqual(5, len(self.output_buffer))

    def test_safe_empty_no_contents(self):
        self.output_buffer = OutputBuffer(enable_buffering=False)
        self.output_buffer.safe_empty()

    def test_safe_empty_buffering(self):
        messages = [
            helpers.generate_bytearray(10),
            helpers.generate_bytearray(10)
        ]
        for message in messages:
            self.output_buffer.enqueue_msgbytes(message)

        self.assertEqual(20, len(self.output_buffer))
        self.assertEqual(OutputBuffer.EMPTY, self.output_buffer.get_buffer())

        self.output_buffer.safe_empty()
        self.assertEqual(0, len(self.output_buffer))
        self.assertEqual(OutputBuffer.EMPTY, self.output_buffer.get_buffer())

