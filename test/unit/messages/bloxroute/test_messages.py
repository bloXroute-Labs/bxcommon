from bxcommon.constants import HDR_COMMON_OFF
from bxcommon.messages.bloxroute.message import Message
from bxcommon.test_utils.abstract_test_case import AbstractTestCase


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
        self.assertEqual(self.payload_len1, self.message1._payload_len)
        message2_rawbytes = self.message2.rawbytes()
        self.assertEqual(self.payload_len2, self.message2._payload_len)
        self.assertEqual(message2_rawbytes, memoryview(self.message2._memoryview))

    def test_msg_type(self):
        self.assertEqual(self.msg_type1, self.message1.msg_type())

    def test_payload_len(self):
        self.assertEqual(self.payload_len1, self.message1.payload_len())

    def test_payload(self):
        self.assertIsNone(self.message1._payload)
        self.assertEqual(self.buf1[HDR_COMMON_OFF:self.payload_len1 + HDR_COMMON_OFF], self.message1.payload())
        self.assertEqual(self.buf1[HDR_COMMON_OFF:self.payload_len1 + HDR_COMMON_OFF], self.message1._payload)
