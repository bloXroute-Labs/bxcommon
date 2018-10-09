import unittest
from bxcommon.utils.buffers.input_buffer import InputBuffer
from collections import deque


class TestInputBuffer(unittest.TestCase):

    def test_init(self):
        in_buf = InputBuffer()
        self.assertEqual(in_buf.length, 0)
        self.assertEqual(in_buf.input_list, deque())

    def test_endswith(self):
        in_buf = InputBuffer()
        self.assertFalse(in_buf.endswith(5))
        in_buf.add_bytes(bytearray([1, 2, 3, 4, 5, 6]))
        self.assertTrue(in_buf.endswith(bytearray([5, 6])))
        self.assertFalse(in_buf.endswith(bytearray([4, 6])))
        with self.assertRaises(ValueError):
            in_buf.endswith([5, 6])
        with self.assertRaises(ValueError):
            in_buf.endswith(bytearray([0, 1, 2, 3, 4, 5, 6]))

    def test_add_bytes(self):
        length_to_add = 12
        in_buf = InputBuffer()
        piece = bytearray([1] * length_to_add)
        in_buf.add_bytes(piece)
        self.assertEqual(in_buf.length, length_to_add)

    def test_remove_bytes(self):
        in_buf = InputBuffer()
        with self.assertRaises(ValueError):
            in_buf.remove_bytes(5)
        with self.assertRaises(ValueError):
            in_buf.remove_bytes(0)
        with self.assertRaises(ValueError):
            in_buf.remove_bytes('f')

        in_buf = self.make_input_buffer()

        self.assertEqual(in_buf.remove_bytes(5), bytearray([i for i in range(1, 6)]))
        self.assertEqual(in_buf.length, 55)
        self.assertEqual(in_buf.remove_bytes(20), bytearray([i for i in range(6, 26)]))
        self.assertEqual(in_buf.length, 35)
        self.assertEqual(in_buf.remove_bytes(35), bytearray([i for i in range(26, 61)]))
        self.assertEqual(in_buf.length, 0)

    def test_peek_message(self):
        in_buf = self.make_input_buffer()

        self.assertEqual(in_buf.peek_message(5), bytearray([i for i in range(1, 6)]))
        self.assertEqual(in_buf.peek_message(30), bytearray([i for i in range(1, 31)]))
        self.assertEqual(in_buf.peek_message(60), bytearray([i for i in range(1, 61)]))
        self.assertEqual(in_buf.peek_message(70), bytearray(0))

    def test_get_slice(self):
        in_buf = self.make_input_buffer()

        with self.assertRaises(ValueError):
            in_buf.get_slice(5, None)
        with self.assertRaises(ValueError):
            in_buf.get_slice(None, 6)
        with self.assertRaises(ValueError):
            in_buf.get_slice(100, 60)

        self.assertEqual(in_buf.get_slice(0, 5), bytearray([i for i in range(1, 6)]))
        self.assertEqual(in_buf.get_slice(10, 31), bytearray([i for i in range(11, 32)]))
        self.assertEqual(in_buf.get_slice(34, 59), bytearray([i for i in range(35, 60)]))

    def make_input_buffer(self):
        in_buf = InputBuffer()

        data1 = bytearray([i for i in range(1, 21)])
        data2 = bytearray([i for i in range(21, 41)])
        data3 = bytearray([i for i in range(41, 61)])

        in_buf.add_bytes(data1)
        in_buf.add_bytes(data2)
        in_buf.add_bytes(data3)

        return in_buf
