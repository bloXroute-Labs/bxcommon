from bxcommon.constants import UL_INT_SIZE_IN_BYTES, NETWORK_NUM_LEN, VERSION_NUM_LEN
from bxcommon.exceptions import PayloadLenError
from bxcommon.messages.bloxroute.ack_message import AckMessage
from bxcommon.messages.bloxroute.bloxroute_message_factory import bloxroute_message_factory
from bxcommon.messages.bloxroute.broadcast_message import BroadcastMessage
from bxcommon.messages.bloxroute.get_txs_message import GetTxsMessage
from bxcommon.messages.bloxroute.hello_message import HelloMessage
from bxcommon.messages.bloxroute.key_message import KeyMessage
from bxcommon.messages.bloxroute.ping_message import PingMessage
from bxcommon.messages.bloxroute.pong_message import PongMessage
from bxcommon.messages.bloxroute.tx_message import TxMessage
from bxcommon.messages.bloxroute.txs_message import TxsMessage
from bxcommon.messages.bloxroute.versioning import versioning
from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.test_utils.helpers import create_input_buffer_with_message, create_input_buffer_with_bytes
from bxcommon.utils import crypto
from bxcommon.utils.crypto import SHA256_HASH_LEN, KEY_SIZE
from bxcommon.utils.object_hash import ObjectHash


class BloxrouteMessageFactory(AbstractTestCase):
    HASH = ObjectHash(crypto.double_sha256("123"))

    def get_message_preview_successfully(self, message, expected_command, expected_payload_length):
        is_full_message, command, payload_length = bloxroute_message_factory.get_message_header_preview(
            create_input_buffer_with_message(message)
        )
        self.assertTrue(is_full_message)
        self.assertEqual(expected_command, command)
        self.assertEqual(expected_payload_length, payload_length)

    def get_message_hash_preview_successfully(self, message, expected_hash):
        is_full_message, msg_hash, _payload_length = bloxroute_message_factory.get_message_hash_preview(
            create_input_buffer_with_message(message)
        )
        self.assertTrue(is_full_message)
        self.assertEqual(expected_hash, msg_hash)

    def create_message_successfully(self, message, message_type):
        result = bloxroute_message_factory.create_message_from_buffer(message.rawbytes())
        self.assertIsInstance(result, message_type)
        return result

    def test_message_preview_success_all_types(self):
        self.get_message_preview_successfully(HelloMessage(1, 2, 3), HelloMessage.MESSAGE_TYPE,
                                              UL_INT_SIZE_IN_BYTES + NETWORK_NUM_LEN + VERSION_NUM_LEN)
        self.get_message_preview_successfully(AckMessage(), AckMessage.MESSAGE_TYPE, 0)
        self.get_message_preview_successfully(PingMessage(), PingMessage.MESSAGE_TYPE, 0)
        self.get_message_preview_successfully(PongMessage(), PongMessage.MESSAGE_TYPE, 0)

        blob = bytearray(1 for _ in xrange(4))
        self.get_message_preview_successfully(BroadcastMessage(self.HASH, 1, blob), BroadcastMessage.MESSAGE_TYPE,
                                              SHA256_HASH_LEN + NETWORK_NUM_LEN + len(blob))
        self.get_message_preview_successfully(TxMessage(self.HASH, 1, blob, sid=12), TxMessage.MESSAGE_TYPE,
                                              SHA256_HASH_LEN + NETWORK_NUM_LEN + UL_INT_SIZE_IN_BYTES + len(blob))
        self.get_message_preview_successfully(KeyMessage(self.HASH, bytearray(1 for _ in range(KEY_SIZE)), 1),
                                              KeyMessage.MESSAGE_TYPE, SHA256_HASH_LEN + KEY_SIZE + NETWORK_NUM_LEN)

        get_txs = [1, 2, 3]
        self.get_message_preview_successfully(GetTxsMessage(get_txs), GetTxsMessage.MESSAGE_TYPE,
                                              UL_INT_SIZE_IN_BYTES + UL_INT_SIZE_IN_BYTES * len(get_txs))

        txs = [(1, crypto.double_sha256("123"), bytearray(4)), (2, crypto.double_sha256("234"), bytearray(8))]
        expected_length = (UL_INT_SIZE_IN_BYTES +
                           sum(UL_INT_SIZE_IN_BYTES + SHA256_HASH_LEN + UL_INT_SIZE_IN_BYTES +
                               len(tx[2]) for tx in txs))
        self.get_message_preview_successfully(TxsMessage(txs), TxsMessage.MESSAGE_TYPE, expected_length)

    def test_message_preview_incomplete(self):
        message = HelloMessage(1, 2, 3)
        is_full_message, command, payload_length = bloxroute_message_factory.get_message_header_preview(
            create_input_buffer_with_bytes(message.rawbytes()[:-1])
        )
        self.assertFalse(is_full_message)
        self.assertEquals("hello", command)
        self.assertEquals(VERSION_NUM_LEN + UL_INT_SIZE_IN_BYTES  + NETWORK_NUM_LEN, payload_length)

        is_full_message, command, payload_length = bloxroute_message_factory.get_message_header_preview(
            create_input_buffer_with_bytes(message.rawbytes()[:1])
        )
        self.assertFalse(is_full_message)
        self.assertIsNone(command)
        self.assertIsNone(payload_length)

    def test_message_hash_preview(self):
        dummy_network_num = 12345
        blob = bytearray(1 for _ in xrange(4))
        self.get_message_hash_preview_successfully(BroadcastMessage(self.HASH, dummy_network_num, blob), self.HASH)
        self.get_message_hash_preview_successfully(TxMessage(self.HASH, dummy_network_num, blob, sid=12), self.HASH)
        self.get_message_hash_preview_successfully(KeyMessage(self.HASH, bytearray(1 for _ in range(KEY_SIZE)), dummy_network_num),
                                                   self.HASH)

    def test_message_hash_preview_incomplete(self):
        blob = bytearray(1 for _ in xrange(4))
        broadcast_message = BroadcastMessage(self.HASH, 123, blob)

        is_full_message, msg_hash, payload_length = bloxroute_message_factory.get_message_hash_preview(
            create_input_buffer_with_bytes(broadcast_message.rawbytes()[:-1])
        )
        self.assertFalse(is_full_message)
        self.assertEquals(self.HASH, msg_hash)
        self.assertEquals(SHA256_HASH_LEN + NETWORK_NUM_LEN + len(blob), payload_length)

        is_full_message, msg_hash, payload_length = bloxroute_message_factory.get_message_hash_preview(
            create_input_buffer_with_bytes(broadcast_message.rawbytes()[:-12])
        )
        self.assertFalse(is_full_message)
        self.assertIsNone(msg_hash)
        self.assertIsNone(payload_length)

    def test_create_message_success_all_types(self):
        test_network_num = 10
        test_protocol_version = versioning.CURRENT_PROTOCOL_VERSION

        hello_message = self.create_message_successfully(HelloMessage(protocol_version=test_protocol_version,
                                                                      idx=1,
                                                                      network_num=test_network_num), HelloMessage)
        self.assertEqual(test_protocol_version, hello_message.protocol_version())
        self.assertEqual(1, hello_message.idx())
        self.assertEqual(test_network_num, hello_message.network_num())
        self.create_message_successfully(AckMessage(), AckMessage)
        self.create_message_successfully(PingMessage(), PingMessage)
        self.create_message_successfully(PongMessage(), PongMessage)

        blob = bytes(4)
        broadcast_message = self.create_message_successfully(BroadcastMessage(self.HASH,
                                                                              network_num=test_network_num,
                                                                              blob=blob),
                                                             BroadcastMessage)
        self.assertEqual(self.HASH, broadcast_message.msg_hash())
        self.assertEqual(test_network_num, broadcast_message.network_num())
        self.assertEqual(blob, broadcast_message.blob())

        sid = 12
        tx_val = bytes(1 for _ in range(5))
        tx_message = self.create_message_successfully(TxMessage(self.HASH,
                                                                network_num=test_network_num,
                                                                tx_val=tx_val,
                                                                sid=sid),
                                                      TxMessage)
        self.assertEqual(self.HASH, tx_message.tx_hash())
        self.assertEqual(sid, tx_message.short_id())
        self.assertEqual(test_network_num, tx_message.network_num())
        self.assertEqual(tx_val, tx_message.tx_val())

        key = bytearray(1 for _ in range(KEY_SIZE))
        key_message = self.create_message_successfully(
            KeyMessage(self.HASH, bytearray(1 for _ in range(KEY_SIZE)), network_num=test_network_num),
            KeyMessage)
        self.assertEqual(key, key_message.key())
        self.assertEqual(test_network_num, key_message.network_num())
        self.assertEqual(self.HASH, key_message.msg_hash())

        get_txs = [1, 2, 3]
        get_txs_message = self.create_message_successfully(GetTxsMessage(get_txs), GetTxsMessage)
        self.assertEqual(get_txs, get_txs_message.get_short_ids())

        txs = [(1, crypto.double_sha256("123"), bytearray(4)), (2, crypto.double_sha256("234"), bytearray(8))]
        txs_message = self.create_message_successfully(TxsMessage(txs), TxsMessage)
        result_txs = [(1, ObjectHash(crypto.double_sha256("123")), bytearray(4)),
                      (2, ObjectHash(crypto.double_sha256("234")), bytearray(8))]
        self.assertEqual(result_txs, txs_message.get_txs())

    def test_create_message_failure(self):
        message = HelloMessage(1, 2, 3)
        with self.assertRaises(PayloadLenError):
            bloxroute_message_factory.create_message_from_buffer(message.rawbytes()[:-1])
