from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.utils import convert


class ConvertTests(AbstractTestCase):

    def test_str_to_bool(self):
        self.assertTrue(convert.str_to_bool("True"))
        self.assertTrue(convert.str_to_bool("true"))
        self.assertTrue(convert.str_to_bool("1"))
        self.assertFalse(convert.str_to_bool("False"))
        self.assertFalse(convert.str_to_bool("false"))
        self.assertFalse(convert.str_to_bool("0"))
        self.assertFalse(convert.str_to_bool("dummy_text"))
        self.assertFalse(convert.str_to_bool(None))

    def test_bytes_to_hex(self):
        self.assertEqual("00", convert.bytes_to_hex(b"\x00"))
        self.assertEqual("0001", convert.bytes_to_hex(b"\x00\x01"))
        self.assertEqual("0001ab", convert.bytes_to_hex(b"\x00\x01\xab"))

    def test_hex_to_bytes(self):
        self.assertEqual(b"\x00", convert.hex_to_bytes(b"00"))
        self.assertEqual(b"\x00\x01", convert.hex_to_bytes(b"0001"))
        self.assertEqual(b"\x00\x01\xab", convert.hex_to_bytes(b"0001ab"))


