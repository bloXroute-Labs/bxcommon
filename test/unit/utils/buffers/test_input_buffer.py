import unittest
from bxcommon.utils.buffers.input_buffer import InputBuffer
from collections import deque


class TestInputBuffer(unittest.TestCase):

    def setUp(self):
        self.in_buf = InputBuffer()
        self.length_to_add = 20
        self.data1 = bytearray([i for i in range(1, 21)])
        self.data2 = bytearray([i for i in range(21, 41)])
        self.data3 = bytearray([i for i in range(41, 61)])

    def test_endswith(self):
        self.assertFalse(self.in_buf.endswith(5))
        self.in_buf.add_bytes(bytearray([1, 2, 3, 4, 5, 6]))
        self.assertTrue(self.in_buf.endswith(bytearray([5, 6])))
        self.assertFalse(self.in_buf.endswith(bytearray([4, 6])))
        with self.assertRaises(ValueError):
            self.in_buf.endswith([5, 6])

        self.assertEqual(self.in_buf.endswith(bytearray([0, 1, 2, 3, 4, 5, 6])), False)

        self.assertEqual(True, self.in_buf.endswith(bytearray(0)))

    def test_add_bytes(self):
        self.in_buf.add_bytes(self.data1)
        self.in_buf.add_bytes(self.data2)

        self.assertEqual(2 * self.length_to_add, self.in_buf.length)
        self.assertEqual(deque([self.data1, self.data2]), self.in_buf.input_list)

    def test_remove_bytes(self):
        with self.assertRaises(ValueError):
            self.in_buf.remove_bytes(5)
        with self.assertRaises(ValueError):
            self.in_buf.remove_bytes(0)
        with self.assertRaises(ValueError):
            self.in_buf.remove_bytes("f")

        self.make_input_buffer()

        self.assertEqual(bytearray([i for i in range(1, 6)]), self.in_buf.remove_bytes(5))
        self.assertEqual(55, self.in_buf.length, 55)
        self.assertEqual(bytearray([i for i in range(6, 26)]), self.in_buf.remove_bytes(20))
        self.assertEqual(35, self.in_buf.length)
        self.assertEqual(bytearray([i for i in range(26, 61)]), self.in_buf.remove_bytes(35))
        self.assertEqual(0, self.in_buf.length)

    def test_peek_message(self):
        self.make_input_buffer()
        # Edge Case: peek_message returns bytearray(0) when it peeks a number greater than the message length.
        self.assertEqual(bytearray(0), self.in_buf.peek_message(70))

        self.assertIn(bytearray([i for i in range(1, 5)]), self.in_buf.peek_message(5))
        self.assertIn(bytearray([i for i in range(1, 31)]), self.in_buf.peek_message(30))
        self.assertIn(bytearray([i for i in range(1, 61)]), self.in_buf.peek_message(60))

    def test_get_slice(self):
        self.make_input_buffer()

        with self.assertRaises(ValueError):
            self.in_buf.get_slice(5, None)
        with self.assertRaises(ValueError):
            self.in_buf.get_slice(None, 6)
        with self.assertRaises(ValueError):
            self.in_buf.get_slice(100, 60)

        self.assertEqual(bytearray([i for i in range(1, 6)]), self.in_buf.get_slice(0, 5))
        self.assertEqual(bytearray([i for i in range(11, 32)]), self.in_buf.get_slice(10, 31))
        self.assertEqual(bytearray([i for i in range(35, 60)]), self.in_buf.get_slice(34, 59))

    def make_input_buffer(self):
        self.in_buf.add_bytes(self.data1)
        self.in_buf.add_bytes(self.data2)
        self.in_buf.add_bytes(self.data3)

