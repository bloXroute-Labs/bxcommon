import unittest

from bxcommon.utils.object_hash import ObjectHash


class ObjectHashTests(unittest.TestCase):

    def setUp(self):
        self.hash_0_to_31 = ObjectHash(bytearray([i for i in range(32)]))
        self.hash_0_to_31_2 = ObjectHash(bytearray([i for i in range(32)]))
        self.hash_1_to_32 = ObjectHash(bytearray([i for i in range(1, 33)]))
        self.hash_zeros = ObjectHash(bytearray([0] * 32))

    def test_init(self):

        with self.assertRaises(AssertionError):
            ObjectHash(bytearray([i for i in range(1, 20)]))
        with self.assertRaises(AssertionError):
            ObjectHash(bytearray())

    def test_hash(self):

        self.assertEqual(hash(self.hash_0_to_31), hash(self.hash_0_to_31_2))
        self.assertNotEqual(hash(self.hash_0_to_31), hash(self.hash_1_to_32))

    def test_cmp(self):

        self.assertTrue(self.hash_0_to_31 == self.hash_0_to_31_2)
        self.assertTrue(self.hash_1_to_32 > self.hash_0_to_31)
        self.assertTrue(self.hash_zeros < self.hash_0_to_31_2)

    def test_get_item(self):

        self.assertEqual(self.hash_0_to_31[4], self.hash_0_to_31_2[4])
        self.assertEqual(self.hash_0_to_31[5], 5)
        self.assertEqual(self.hash_0_to_31_2[25], 25)
        self.assertEqual(self.hash_1_to_32[10], 11)
        self.assertEqual(self.hash_zeros[20], 0)

    def test_repr(self):

        self.assertEqual(repr(self.hash_0_to_31), repr(self.hash_0_to_31_2))
        self.assertNotEqual(repr(self.hash_0_to_31), repr(self.hash_1_to_32))
        self.assertNotEqual(repr(self.hash_0_to_31_2), repr(self.hash_zeros))
        self.assertNotEqual(repr(self.hash_1_to_32), repr(self.hash_0_to_31_2))


