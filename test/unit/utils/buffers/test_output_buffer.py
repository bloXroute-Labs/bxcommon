import unittest
from bxcommon.utils.buffers.output_buffer import OutputBuffer
from collections import deque


class TestOutputBuffer(unittest.TestCase):
    def test_init(self):
        out_buf = OutputBuffer()
        self.assertEqual(out_buf.output_msgs, deque())
        self.assertEqual(out_buf.index, 0)
        self.assertEqual(out_buf.length, 0)

    def test_get_buffer(self):
        out_buf = OutputBuffer()

        with self.assertRaises(RuntimeError):
            out_buf.get_buffer()

        data1 = bytearray([i for i in range(20)])
        out_buf.enqueue_msgbytes(data1)
        self.assertEqual(out_buf.get_buffer(), data1)

        data2 = bytearray([i for i in range(20, 40)])
        out_buf.enqueue_msgbytes(data2)
        self.assertEqual(out_buf.get_buffer(), data1)

        new_index = 10
        out_buf.index = new_index
        self.assertEqual(out_buf.get_buffer(), data1[new_index:])

    def test_advance_buffer(self):
        out_buf = OutputBuffer()
        with self.assertRaises(ValueError):
            out_buf.advance_buffer(5)

        data1 = bytearray([i for i in range(20)])
        out_buf.enqueue_msgbytes(data1)
        data2 = bytearray([i for i in range(20, 40)])
        out_buf.enqueue_msgbytes(data2)

        out_buf.advance_buffer(10)
        self.assertEqual(out_buf.index, 10)
        self.assertEqual(out_buf.length, 30)

        out_buf.advance_buffer(10)
        self.assertEqual(out_buf.index, 0)
        self.assertEqual(len(out_buf.output_msgs), 1)

    def test_at_msg_boundary(self):
        out_buf = OutputBuffer()
        self.assertTrue(out_buf.at_msg_boundary())
        out_buf.index = 1
        self.assertFalse(out_buf.at_msg_boundary())

    def test_enqueue_msgbytes(self):
        out_buf = OutputBuffer()
        with self.assertRaises(ValueError):
            out_buf.enqueue_msgbytes('f')

        data1 = bytearray([i for i in range(20)])
        out_buf.enqueue_msgbytes(data1)
        self.assertEqual(out_buf.get_buffer(), data1)

        data2 = bytearray([i for i in range(20, 40)])
        out_buf.enqueue_msgbytes(data2)
        self.assertEqual(out_buf.get_buffer(), data1)

        new_index = 10
        out_buf.index = new_index
        self.assertEqual(out_buf.get_buffer(), data1[new_index:])

    def test_prepend_msg(self):
        out_buf = OutputBuffer()
        with self.assertRaises(ValueError):
            out_buf.prepend_msg('f')

        data1 = bytearray([i for i in range(20)])
        out_buf.prepend_msg(data1)

        data2 = bytearray([i for i in range(20, 40)])
        out_buf.prepend_msg(data2)

        confirm1 = deque()
        confirm1.append(data2)
        confirm1.append(data1)

        self.assertEqual(out_buf.output_msgs, confirm1)
        self.assertEqual(out_buf.length, 40)

        out_buf.advance_buffer(10)

        data3 = bytearray([i for i in range(40, 60)])
        out_buf.prepend_msg(data3)

        confirm2 = deque()
        confirm2.append(data2)
        confirm2.append(data3)
        confirm2.append(data1)

        self.assertEqual(out_buf.output_msgs, confirm2)
        self.assertEqual(out_buf.length, 50)

    def test_has_more_bytes(self):
        out_buf = OutputBuffer()
        self.assertFalse(out_buf.has_more_bytes())
        out_buf.length = 1
        self.assertTrue(out_buf.has_more_bytes())
