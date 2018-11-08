import time

from bxcommon.constants import BTC_HEADER_MINUS_CHECKSUM, BTC_HDR_COMMON_OFF
from bxcommon.exceptions import PayloadLenError, ChecksumError
from bxcommon.messages.btc.addr_btc_message import AddrBTCMessage
from bxcommon.messages.btc.block_btc_message import BlockBTCMessage
from bxcommon.messages.btc.btc_message_factory import btc_message_factory
from bxcommon.messages.btc.data_btc_message import GetHeadersBTCMessage, GetBlocksBTCMessage
from bxcommon.messages.btc.get_addr_btc_message import GetAddrBTCMessage
from bxcommon.messages.btc.header_btc_message import HeadersBTCMessage
from bxcommon.messages.btc.inventory_btc_message import InvBTCMessage, GetDataBTCMessage, NotFoundBTCMessage
from bxcommon.messages.btc.ping_btc_message import PingBTCMessage
from bxcommon.messages.btc.pong_btc_message import PongBTCMessage
from bxcommon.messages.btc.reject_btc_message import RejectBTCMessage
from bxcommon.messages.btc.send_headers_btc_message import SendHeadersBTCMessage
from bxcommon.messages.btc.tx_btc_message import TxIn, TxBTCMessage
from bxcommon.messages.btc.ver_ack_btc_message import VerAckBTCMessage
from bxcommon.messages.btc.version_btc_message import VersionBTCMessage
from bxcommon.test_utils import helpers
from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.test_utils.helpers import create_input_buffer_with_bytes, create_input_buffer_with_message
from bxcommon.utils import crypto
from bxcommon.utils.object_hash import BTCObjectHash


class BtcMessageFactoryTest(AbstractTestCase):
    MAGIC = 12345
    VERSION = 11111
    HASH = BTCObjectHash(binary=crypto.bitcoin_hash("123"))

    VERSION_BTC_MESSAGE = VersionBTCMessage(MAGIC, VERSION, "127.0.0.1", 8000, "127.0.0.1", 8001, 123, 0, "hello")

    def peek_message_successfully(self, message, expected_command, expected_payload_length):
        is_full_message, command, payload_length = btc_message_factory.get_message_header_preview(
            create_input_buffer_with_message(message)
        )
        self.assertTrue(is_full_message)
        self.assertEqual(expected_command, command)
        self.assertEqual(expected_payload_length, payload_length)

    def parse_message_successfully(self, message, message_type):
        result = btc_message_factory.create_message_from_buffer(message.rawbytes())
        self.assertIsInstance(result, message_type)
        return result

    def test_peek_message_success_all_types(self):
        # TODO: pull these numbers into constants, along with all the BTC messages
        self.peek_message_successfully(self.VERSION_BTC_MESSAGE, VersionBTCMessage.MESSAGE_TYPE, 90)
        self.peek_message_successfully(VerAckBTCMessage(self.MAGIC), VerAckBTCMessage.MESSAGE_TYPE, 0)
        self.peek_message_successfully(PingBTCMessage(self.MAGIC), PingBTCMessage.MESSAGE_TYPE, 8)
        self.peek_message_successfully(PongBTCMessage(self.MAGIC, 123), PongBTCMessage.MESSAGE_TYPE, 8)
        self.peek_message_successfully(GetAddrBTCMessage(self.MAGIC), GetAddrBTCMessage.MESSAGE_TYPE, 0)
        self.peek_message_successfully(AddrBTCMessage(self.MAGIC, [(time.time(), "127.0.0.1", 8000)]),
                                       AddrBTCMessage.MESSAGE_TYPE, 23)

        inv_vector = [(1, self.HASH), (2, self.HASH)]
        self.peek_message_successfully(InvBTCMessage(self.MAGIC, inv_vector), InvBTCMessage.MESSAGE_TYPE, 73)
        self.peek_message_successfully(GetDataBTCMessage(self.MAGIC, inv_vector), GetDataBTCMessage.MESSAGE_TYPE, 73)
        self.peek_message_successfully(NotFoundBTCMessage(self.MAGIC, inv_vector), NotFoundBTCMessage.MESSAGE_TYPE, 73)

        hashes = [self.HASH, self.HASH]
        self.peek_message_successfully(GetHeadersBTCMessage(self.MAGIC, self.VERSION, hashes, self.HASH),
                                       GetHeadersBTCMessage.MESSAGE_TYPE, 101)
        self.peek_message_successfully(GetBlocksBTCMessage(self.MAGIC, self.VERSION, hashes, self.HASH),
                                       GetBlocksBTCMessage.MESSAGE_TYPE, 101)

        self.peek_message_successfully(TxBTCMessage(self.MAGIC, self.VERSION, [], [], 0), TxBTCMessage.MESSAGE_TYPE, 10)

        txs = [TxIn(buf=bytearray(10), length=10, off=0).rawbytes()] * 5
        self.peek_message_successfully(BlockBTCMessage(self.MAGIC, self.VERSION, self.HASH, self.HASH, 0, 0, 0, txs),
                                       BlockBTCMessage.MESSAGE_TYPE, 131)
        self.peek_message_successfully(HeadersBTCMessage(self.MAGIC, [helpers.generate_bytearray(81)] * 2),
                                       HeadersBTCMessage.MESSAGE_TYPE, 163)
        self.peek_message_successfully(RejectBTCMessage(self.MAGIC, "a message", RejectBTCMessage.REJECT_MALFORMED,
                                                        "test break", helpers.generate_bytearray(10)),
                                       RejectBTCMessage.MESSAGE_TYPE, 32)
        self.peek_message_successfully(SendHeadersBTCMessage(self.MAGIC), SendHeadersBTCMessage.MESSAGE_TYPE, 0)

    def test_peek_message_incomplete(self):
        is_full_message, command, payload_length = btc_message_factory.get_message_header_preview(
            create_input_buffer_with_bytes(self.VERSION_BTC_MESSAGE.rawbytes()[:-10])
        )
        self.assertFalse(is_full_message)
        self.assertEquals("version", command)
        self.assertEquals(90, payload_length)

        is_full_message, command, payload_length = btc_message_factory.get_message_header_preview(
            create_input_buffer_with_bytes(self.VERSION_BTC_MESSAGE.rawbytes()[:1])
        )
        self.assertFalse(is_full_message)
        self.assertIsNone(command)
        self.assertIsNone(payload_length)

    def test_parse_message_success_all_types(self):
        # TODO: pull these numbers into constants, along with all the BTC messages
        self.parse_message_successfully(self.VERSION_BTC_MESSAGE, VersionBTCMessage)
        self.parse_message_successfully(VerAckBTCMessage(self.MAGIC), VerAckBTCMessage)
        self.parse_message_successfully(PingBTCMessage(self.MAGIC), PingBTCMessage)
        self.parse_message_successfully(PongBTCMessage(self.MAGIC, 123), PongBTCMessage)
        self.parse_message_successfully(GetAddrBTCMessage(self.MAGIC), GetAddrBTCMessage)
        self.parse_message_successfully(AddrBTCMessage(self.MAGIC, [(time.time(), "127.0.0.1", 8000)]), AddrBTCMessage)

        inv_vector = [(1, self.HASH), (2, self.HASH)]
        self.parse_message_successfully(InvBTCMessage(self.MAGIC, inv_vector), InvBTCMessage)
        self.parse_message_successfully(GetDataBTCMessage(self.MAGIC, inv_vector), GetDataBTCMessage)
        self.parse_message_successfully(NotFoundBTCMessage(self.MAGIC, inv_vector), NotFoundBTCMessage)

        hashes = [self.HASH, self.HASH]
        self.parse_message_successfully(GetHeadersBTCMessage(self.MAGIC, self.VERSION, hashes, self.HASH),
                                        GetHeadersBTCMessage)
        self.parse_message_successfully(GetBlocksBTCMessage(self.MAGIC, self.VERSION, hashes, self.HASH),
                                        GetBlocksBTCMessage)

        self.parse_message_successfully(TxBTCMessage(self.MAGIC, self.VERSION, [], [], 0), TxBTCMessage)

        txs = [TxIn(buf=bytearray(10), length=10, off=0).rawbytes()] * 5
        self.parse_message_successfully(BlockBTCMessage(self.MAGIC, self.VERSION, self.HASH, self.HASH, 0, 0, 0, txs),
                                        BlockBTCMessage)
        self.parse_message_successfully(HeadersBTCMessage(self.MAGIC, [helpers.generate_bytearray(81)] * 2),
                                        HeadersBTCMessage)
        self.parse_message_successfully(RejectBTCMessage(self.MAGIC, "a message", RejectBTCMessage.REJECT_MALFORMED,
                                                         "test break", helpers.generate_bytearray(10)),
                                        RejectBTCMessage)
        self.parse_message_successfully(SendHeadersBTCMessage(self.MAGIC), SendHeadersBTCMessage)

    def test_parse_message_incomplete(self):
        with self.assertRaises(PayloadLenError):
            btc_message_factory.create_message_from_buffer(PingBTCMessage(self.MAGIC).rawbytes()[:-1])

        ping_message = PingBTCMessage(self.MAGIC)
        for i in xrange(BTC_HEADER_MINUS_CHECKSUM, BTC_HDR_COMMON_OFF):
            ping_message.buf[i] = 0
        with self.assertRaises(ChecksumError):
            btc_message_factory.create_message_from_buffer(ping_message.rawbytes())
