from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.messages.message import Message


class MessageTest(AbstractTestCase):

    def setUp(self):
        self.buf1 = bytearray(40)
        self.payload_len1 = 20
        self.msg_type1 = "example"
        self.message1 = Message(self.msg_type1, self.payload_len1, self.buf1)
        self.message2 = Message(buf=bytearray(20), msg_type='hello', payload_len=50)

    def test_init(self):
        self.assertEqual(self.buf1, self.message1.buf)
        self.assertEqual(self.buf1, self.message1._memoryview)
        self.assertEqual(self.msg_type1, self.message1._msg_type)
        self.assertIsNone(self.message1._payload)
        self.assertEqual(self.payload_len1, self.message1._payload_len)

    def test_rawbytes(self):
        self.assertEqual(type(self.message1.rawbytes()), memoryview)
        self.assertEqual(self.message1._payload_len, 20)
        message2_rawbytes = self.message2.rawbytes()
        self.assertEqual(self.message2._payload_len, 50)
        self.assertEqual(message2_rawbytes, memoryview(self.message2._memoryview))

    def test_peek_message(self):
        pass

    def test_parse(self):
        pass

    def test_msg_type(self):
        self.assertEqual(self.msg_type1, self.message1.msg_type())

    def test_payload_len(self):
        self.assertEqual(self.payload_len1, self.message1.payload_len())

    def test_payload(self):
        message_test_payload = Message(buf=bytearray(20), msg_type='hello', payload_len=20)
        self.assertEqual(message_test_payload._payload, None)
        self.assertEqual(message_test_payload.payload(), bytearray(4))


