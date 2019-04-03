from collections import deque

from bxcommon.constants import UL_INT_SIZE_IN_BYTES, NETWORK_NUM_LEN, NODE_ID_SIZE_IN_BYTES, \
    HDR_COMMON_OFF, BLOCK_ENCRYPTED_FLAG_LEN
from bxcommon.exceptions import PayloadLenError
from bxcommon.messages.bloxroute.ack_message import AckMessage
from bxcommon.messages.bloxroute.bloxroute_message_factory import bloxroute_message_factory
from bxcommon.messages.bloxroute.bloxroute_version_manager import bloxroute_version_manager
from bxcommon.messages.bloxroute.broadcast_message import BroadcastMessage
from bxcommon.messages.bloxroute.get_txs_message import GetTxsMessage
from bxcommon.messages.bloxroute.hello_message import HelloMessage
from bxcommon.messages.bloxroute.key_message import KeyMessage
from bxcommon.messages.bloxroute.ping_message import PingMessage
from bxcommon.messages.bloxroute.pong_message import PongMessage
from bxcommon.messages.bloxroute.tx_message import TxMessage
from bxcommon.messages.bloxroute.txs_message import TxsMessage
from bxcommon.messages.bloxroute.version_message import VersionMessage
from bxcommon.models.transaction_info import TransactionInfo
from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.test_utils.helpers import create_input_buffer_with_message, create_input_buffer_with_bytes
from bxcommon.utils import crypto
from bxcommon.utils.crypto import SHA256_HASH_LEN, KEY_SIZE
from bxcommon.utils.object_hash import Sha256Hash


class BloxrouteMessageFactory(AbstractTestCase):
    HASH = Sha256Hash(crypto.double_sha256(b"123"))
    NETWORK_NUM = 12345

    def get_message_preview_successfully(self, message, expected_command, expected_payload_length):
        is_full_message, command, payload_length = bloxroute_message_factory.get_message_header_preview_from_input_buffer(
            create_input_buffer_with_message(message)
        )
        self.assertTrue(is_full_message)
        self.assertEqual(expected_command, command)
        self.assertEqual(expected_payload_length, payload_length)

    def get_hashed_message_preview_successfully(self, message, expected_hash):
        is_full_message, msg_hash, network_num, _payload_length = \
            bloxroute_message_factory.get_hashed_message_preview_from_input_buffer(
                create_input_buffer_with_bytes(message.rawbytes()[:HDR_COMMON_OFF + SHA256_HASH_LEN + NETWORK_NUM_LEN])
            )
        self.assertTrue(is_full_message)
        self.assertEqual(expected_hash, msg_hash)
        self.assertEqual(self.NETWORK_NUM, network_num)

    def create_message_successfully(self, message, message_type):
        result = bloxroute_message_factory.create_message_from_buffer(message.rawbytes())
        self.assertIsInstance(result, message_type)
        return result

    def test_message_hello(self):
        hello_msg = HelloMessage(protocol_version=bloxroute_version_manager.CURRENT_PROTOCOL_VERSION,
                                 network_num=1,
                                 node_id="c2b04fd2-7c81-432b-99a5-8b68f43d97e8")
        self.assertEqual(hello_msg.node_id(), "c2b04fd2-7c81-432b-99a5-8b68f43d97e8")
        self.assertEqual(hello_msg.network_num(), 1)

    def test_message_preview_success_all_types(self):
        self.get_message_preview_successfully(HelloMessage(protocol_version=1, network_num=2),
                                              HelloMessage.MESSAGE_TYPE,
                                              VersionMessage.VERSION_MESSAGE_LENGTH + UL_INT_SIZE_IN_BYTES +
                                              NODE_ID_SIZE_IN_BYTES - UL_INT_SIZE_IN_BYTES)
        self.get_message_preview_successfully(AckMessage(), AckMessage.MESSAGE_TYPE, 0)
        self.get_message_preview_successfully(PingMessage(), PingMessage.MESSAGE_TYPE, 8)
        self.get_message_preview_successfully(PongMessage(), PongMessage.MESSAGE_TYPE, 8)

        blob = bytearray(1 for _ in range(4))
        self.get_message_preview_successfully(BroadcastMessage(self.HASH, 1, True, blob), BroadcastMessage.MESSAGE_TYPE,
                                              SHA256_HASH_LEN + NETWORK_NUM_LEN + BLOCK_ENCRYPTED_FLAG_LEN + len(blob))
        self.get_message_preview_successfully(TxMessage(self.HASH, 1, 12, blob), TxMessage.MESSAGE_TYPE,
                                              SHA256_HASH_LEN + NETWORK_NUM_LEN + UL_INT_SIZE_IN_BYTES + len(blob))
        self.get_message_preview_successfully(KeyMessage(self.HASH, 1, bytearray(1 for _ in range(KEY_SIZE))),
                                              KeyMessage.MESSAGE_TYPE, SHA256_HASH_LEN + KEY_SIZE + NETWORK_NUM_LEN)

        get_txs = [1, 2, 3]
        self.get_message_preview_successfully(GetTxsMessage(get_txs), GetTxsMessage.MESSAGE_TYPE,
                                              UL_INT_SIZE_IN_BYTES + UL_INT_SIZE_IN_BYTES * len(get_txs))

        txs = deque([TransactionInfo(crypto.double_sha256(b"123"), bytearray(4), 1),
                     TransactionInfo(crypto.double_sha256(b"234"), bytearray(8), 2)])
        expected_length = (UL_INT_SIZE_IN_BYTES +
                           sum(UL_INT_SIZE_IN_BYTES + SHA256_HASH_LEN + UL_INT_SIZE_IN_BYTES +
                               len(tx.contents) for tx in txs))
        self.get_message_preview_successfully(TxsMessage(txs), TxsMessage.MESSAGE_TYPE, expected_length)

    def test_message_preview_incomplete(self):
        message = HelloMessage(protocol_version=1, network_num=2)
        is_full_message, command, payload_length = bloxroute_message_factory.get_message_header_preview_from_input_buffer(
            create_input_buffer_with_bytes(message.rawbytes()[:-1])
        )
        self.assertFalse(is_full_message)
        self.assertEqual(b"hello", command)
        self.assertEqual(VersionMessage.VERSION_MESSAGE_LENGTH + UL_INT_SIZE_IN_BYTES + NODE_ID_SIZE_IN_BYTES -
                          UL_INT_SIZE_IN_BYTES, payload_length)

        is_full_message, command, payload_length = bloxroute_message_factory.get_message_header_preview_from_input_buffer(
            create_input_buffer_with_bytes(message.rawbytes()[:1])
        )
        self.assertFalse(is_full_message)
        self.assertIsNone(command)
        self.assertIsNone(payload_length)

    def test_message_hash_preview(self):
        blob = bytearray(1 for _ in range(4))
        self.get_hashed_message_preview_successfully(BroadcastMessage(self.HASH, self.NETWORK_NUM, True, blob), self.HASH)

    def test_message_hash_preview_incomplete(self):
        blob = bytearray(1 for _ in range(4))
        broadcast_message = BroadcastMessage(self.HASH, 123, True, blob)

        is_full_message, msg_hash, network_num, payload_length = \
            bloxroute_message_factory.get_hashed_message_preview_from_input_buffer(
                create_input_buffer_with_bytes(broadcast_message.rawbytes()
                                               [:HDR_COMMON_OFF + SHA256_HASH_LEN + NETWORK_NUM_LEN - 1])
            )
        self.assertFalse(is_full_message)
        self.assertIsNone(msg_hash)
        self.assertIsNone(network_num)
        self.assertIsNone(payload_length)

    def test_create_message_success_all_types(self):
        test_network_num = 10
        test_protocol_version = bloxroute_version_manager.CURRENT_PROTOCOL_VERSION

        hello_message = self.create_message_successfully(HelloMessage(protocol_version=test_protocol_version,
                                                                      network_num=test_network_num,
                                                                      ),
                                                         HelloMessage)
        self.assertEqual(test_protocol_version, hello_message.protocol_version())
        self.assertEqual(test_network_num, hello_message.network_num())
        self.create_message_successfully(AckMessage(), AckMessage)
        self.create_message_successfully(PingMessage(), PingMessage)
        self.create_message_successfully(PongMessage(), PongMessage)

        blob = bytes(4)
        broadcast_message = self.create_message_successfully(BroadcastMessage(self.HASH,
                                                                              network_num=test_network_num,
                                                                              is_encrypted=True,
                                                                              blob=blob),
                                                             BroadcastMessage)
        self.assertEqual(self.HASH, broadcast_message.block_hash())
        self.assertEqual(test_network_num, broadcast_message.network_num())
        self.assertTrue(broadcast_message.is_encrypted())
        self.assertEqual(blob, broadcast_message.blob())

        sid = 12
        tx_val = bytes(1 for _ in range(5))
        tx_message = self.create_message_successfully(TxMessage(self.HASH,
                                                                network_num=test_network_num,
                                                                sid=sid,
                                                                tx_val=tx_val),
                                                      TxMessage)
        self.assertEqual(self.HASH, tx_message.tx_hash())
        self.assertEqual(sid, tx_message.short_id())
        self.assertEqual(test_network_num, tx_message.network_num())
        self.assertEqual(tx_val, tx_message.tx_val())

        key = bytearray(1 for _ in range(KEY_SIZE))
        key_message = self.create_message_successfully(
            KeyMessage(self.HASH, test_network_num, bytearray(1 for _ in range(KEY_SIZE))),
            KeyMessage)
        self.assertEqual(key, key_message.key())
        self.assertEqual(test_network_num, key_message.network_num())
        self.assertEqual(self.HASH, key_message.block_hash())

        get_txs = [1, 2, 3]
        get_txs_message = self.create_message_successfully(GetTxsMessage(get_txs), GetTxsMessage)
        self.assertEqual(get_txs, get_txs_message.get_short_ids())

        txs = [TransactionInfo(Sha256Hash(crypto.double_sha256(b"123")), bytearray(4), 1),
               TransactionInfo(Sha256Hash(crypto.double_sha256(b"234")), bytearray(8), 2)]
        txs_message = self.create_message_successfully(TxsMessage(txs), TxsMessage)
        result_txs = txs_message.get_txs()
        for i, result_tx in enumerate(result_txs):
            self.assertEqual(txs[i].hash, result_tx.hash)
            self.assertEqual(txs[i].contents, result_tx.contents)
            self.assertEqual(txs[i].short_id, result_tx.short_id)

    def test_create_message_failure(self):
        message = HelloMessage(protocol_version=1, network_num=2)
        with self.assertRaises(PayloadLenError):
            bloxroute_message_factory.create_message_from_buffer(message.rawbytes()[:-1])
            bloxroute_message_factory.create_message_from_buffer(message.rawbytes()[:-1])

    def test_ping_response_msg(self):
        ping = PingMessage(nonce=50)
        self.assertEqual(50, ping.nonce())
        msg = bloxroute_message_factory.create_message_from_buffer(ping.buf)
        self.assertEqual(50, msg.nonce())

    def test_pong_response_msg(self):
        pong = PongMessage(nonce=50)
        self.assertEqual(50, pong.nonce())
        msg = bloxroute_message_factory.create_message_from_buffer(pong.buf)
