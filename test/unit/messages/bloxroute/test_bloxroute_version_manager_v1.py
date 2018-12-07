from bxcommon.constants import DEFAULT_NETWORK_NUM, NETWORK_NUM_LEN, VERSION_NUM_LEN
from bxcommon.messages.bloxroute.ack_message import AckMessage
from bxcommon.messages.bloxroute.bloxroute_message_factory import bloxroute_message_factory
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.bloxroute_version_manager import bloxroute_version_manager
from bxcommon.messages.bloxroute.broadcast_message import BroadcastMessage
from bxcommon.messages.bloxroute.get_txs_message import GetTxsMessage
from bxcommon.messages.bloxroute.hello_message import HelloMessage
from bxcommon.messages.bloxroute.key_message import KeyMessage
from bxcommon.messages.bloxroute.ping_message import PingMessage
from bxcommon.messages.bloxroute.pong_message import PongMessage
from bxcommon.messages.bloxroute.tx_message import TxMessage
from bxcommon.messages.bloxroute.txs_message import TxsMessage
from bxcommon.messages.bloxroute.v1.bloxroute_message_factory_v1 import bloxroute_message_factory_v1
from bxcommon.messages.bloxroute.v1.broadcast_message_v1 import BroadcastMessageV1
from bxcommon.messages.bloxroute.v1.hello_message_v1 import HelloMessageV1
from bxcommon.messages.bloxroute.v1.key_message_v1 import KeyMessageV1
from bxcommon.messages.bloxroute.v1.tx_message_v1 import TxMessageV1
from bxcommon.test_utils import helpers
from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.utils.buffers.input_buffer import InputBuffer
from bxcommon.utils.crypto import SHA256_HASH_LEN, KEY_SIZE
from bxcommon.utils.object_hash import ObjectHash


def _get_random_hash():
    random_hash_bytes = helpers.generate_bytearray(SHA256_HASH_LEN)

    return ObjectHash(random_hash_bytes)


class BloxrouteVersionManagerV1Test(AbstractTestCase):

    def test_get_connection_protocol_version_v1(self):
        hello_msg_v1 = HelloMessageV1(idx=0)
        input_buffer = InputBuffer()
        input_buffer.add_bytes(hello_msg_v1.rawbytes())

        self.assertEqual(1, bloxroute_version_manager.get_connection_protocol_version(input_buffer))

    def test_get_connection_protocol_version_v2(self):
        hello_msg_v1 = HelloMessage(2, 0, 1)
        input_buffer = InputBuffer()
        input_buffer.add_bytes(hello_msg_v1.rawbytes())

        self.assertEqual(2, bloxroute_version_manager.get_connection_protocol_version(input_buffer))

    def test_convert_message_to_older_version__hello_message_v1(self):
        dummy_idx = 11

        hello_msg = HelloMessage(protocol_version=bloxroute_version_manager.CURRENT_PROTOCOL_VERSION,
                                 idx=dummy_idx,
                                 network_num=DEFAULT_NETWORK_NUM)

        hello_msg_v1 = bloxroute_version_manager.convert_message_to_older_version(1, hello_msg)

        self.assertIsInstance(hello_msg_v1, HelloMessageV1)

        self.assertEqual(len(hello_msg_v1.rawbytes()) + NETWORK_NUM_LEN + VERSION_NUM_LEN, len(hello_msg.rawbytes()))
        self.assertEqual(hello_msg_v1.payload_len() + NETWORK_NUM_LEN + VERSION_NUM_LEN, hello_msg.payload_len())
        self.assertEqual(hello_msg_v1.idx(), hello_msg.idx())
        self.assertEqual(dummy_idx, hello_msg_v1.idx())

    def test_convert_message_from_older_version__hello_message_v1(self):
        dummy_idx = 15

        hello_msg_v1 = HelloMessageV1(idx=dummy_idx)

        hello_msg = bloxroute_version_manager.convert_message_from_older_version(1, hello_msg_v1)

        self.assertIsInstance(hello_msg, HelloMessage)
        self.assertEqual(len(hello_msg_v1.rawbytes()) + NETWORK_NUM_LEN + VERSION_NUM_LEN, len(hello_msg.rawbytes()))
        self.assertEqual(hello_msg_v1.payload_len() + NETWORK_NUM_LEN + VERSION_NUM_LEN, hello_msg.payload_len())

        self.assertEqual(dummy_idx, hello_msg.idx())
        self.assertEqual(1, hello_msg.protocol_version())
        self.assertEqual(DEFAULT_NETWORK_NUM, hello_msg.network_num())

    def test_convert_message_to_older_version__tx_message_v1(self):
        tx_hash = _get_random_hash()
        tx_bytes = helpers.generate_bytearray(12345)

        tx_msg = TxMessage(tx_hash=tx_hash, network_num=DEFAULT_NETWORK_NUM, tx_val=tx_bytes)

        tx_msg_v1 = bloxroute_version_manager.convert_message_to_older_version(1, tx_msg)

        self.assertIsInstance(tx_msg_v1, TxMessageV1)

        self.assertNotEqual(len(tx_msg_v1.rawbytes()), len(tx_msg.rawbytes()))
        self.assertEqual(tx_msg_v1.tx_hash(), tx_msg.tx_hash())
        self.assertEqual(tx_msg_v1.tx_val(), tx_msg.tx_val())

        tx_msg_not_convertable = TxMessage(tx_hash=tx_hash, network_num=12345, tx_val=tx_bytes)
        self.assertRaises(ValueError, bloxroute_version_manager.convert_message_to_older_version, 1,
                          tx_msg_not_convertable)

    def test_convert_message_from_older_version__tx_message_v1(self):
        tx_hash = _get_random_hash()
        tx_bytes = helpers.generate_bytearray(12345)

        tx_msg_v1 = TxMessageV1(tx_hash=tx_hash, tx_val=tx_bytes)

        tx_msg = bloxroute_version_manager.convert_message_from_older_version(1, tx_msg_v1)

        self.assertIsInstance(tx_msg, TxMessage)

        self.assertNotEqual(len(tx_msg_v1.rawbytes()), len(tx_msg.rawbytes()))
        self.assertEqual(tx_msg_v1.tx_hash(), tx_msg.tx_hash())
        self.assertEqual(tx_msg_v1.tx_val(), tx_msg.tx_val())
        self.assertEqual(DEFAULT_NETWORK_NUM, tx_msg.network_num())

    def test_convert_message_to_older_version__key_message_v1(self):
        msg_hash = _get_random_hash()
        key_bytes = helpers.generate_bytearray(KEY_SIZE)

        key_msg = KeyMessage(msg_hash=msg_hash, network_num=DEFAULT_NETWORK_NUM, key=key_bytes)

        key_msg_v1 = bloxroute_version_manager.convert_message_to_older_version(1, key_msg)

        self.assertIsInstance(key_msg_v1, KeyMessageV1)

        self.assertNotEqual(len(key_msg_v1.rawbytes()), len(key_msg.rawbytes()))
        self.assertEqual(key_msg_v1.msg_hash(), key_msg.msg_hash())
        self.assertEqual(key_msg_v1.key(), key_msg.key())

        key_msg_not_convertable = KeyMessage(msg_hash=msg_hash, network_num=12345, key=key_bytes)
        self.assertRaises(ValueError, bloxroute_version_manager.convert_message_to_older_version, 1,
                          key_msg_not_convertable)

    def test_convert_message_from_older_version__key_message_v1(self):
        msg_hash = _get_random_hash()
        key_bytes = helpers.generate_bytearray(KEY_SIZE)

        key_msg_v1 = KeyMessageV1(msg_hash=msg_hash, key=key_bytes)

        key_msg = bloxroute_version_manager.convert_message_from_older_version(1, key_msg_v1)

        self.assertIsInstance(key_msg, KeyMessage)

        self.assertNotEqual(len(key_msg_v1.rawbytes()), len(key_msg.rawbytes()))
        self.assertEqual(key_msg_v1.msg_hash(), key_msg.msg_hash())
        self.assertEqual(key_msg_v1.key(), key_msg.key())
        self.assertEqual(DEFAULT_NETWORK_NUM, key_msg.network_num())

    def test_convert_message_to_older_version__broadcast_message_v1(self):
        random_hash = _get_random_hash()
        random_blob_bytes = helpers.generate_bytearray(12345)
        broadcast_msg = BroadcastMessage(msg_hash=random_hash, network_num=1, blob=random_blob_bytes)

        broadcast_msg_v1 = bloxroute_version_manager.convert_message_to_older_version(1, broadcast_msg)
        self.assertIsInstance(broadcast_msg_v1, BroadcastMessageV1)

        self.assertEqual(broadcast_msg_v1.msg_hash(), broadcast_msg.msg_hash())
        self.assertEqual(broadcast_msg_v1.blob(), broadcast_msg.blob())
        self.assertNotEqual(len(broadcast_msg_v1.rawbytes()), len(broadcast_msg.rawbytes()))

        self.assertEqual(random_hash, broadcast_msg_v1.msg_hash())
        self.assertEqual(random_blob_bytes, broadcast_msg_v1.blob())

    def test_convert_message_from_older_version__broadcast_message_v1(self):
        random_hash_bytes = helpers.generate_bytearray(SHA256_HASH_LEN)
        random_hash = ObjectHash(random_hash_bytes)
        random_blob_bytes = helpers.generate_bytearray(12345)
        broadcast_msg_v1 = BroadcastMessageV1(msg_hash=random_hash, blob=random_blob_bytes)

        broadcast_msg = bloxroute_version_manager.convert_message_from_older_version(1, broadcast_msg_v1)
        self.assertIsInstance(broadcast_msg, BroadcastMessage)

        self.assertEqual(broadcast_msg.msg_hash(), broadcast_msg_v1.msg_hash())
        self.assertEqual(broadcast_msg.blob(), broadcast_msg_v1.blob())

        self.assertEqual(random_hash, broadcast_msg.msg_hash())
        self.assertEqual(random_blob_bytes, broadcast_msg.blob())
        self.assertEqual(DEFAULT_NETWORK_NUM, broadcast_msg.network_num())

    def test_convert_first_bytes__to_older_version__broadcast_message_v1(self):
        random_hash = _get_random_hash()
        random_blob_bytes = helpers.generate_bytearray(12345)
        broadcast_msg = BroadcastMessage(msg_hash=random_hash, network_num=1, blob=random_blob_bytes)
        broadcast_msg_bytes = broadcast_msg.rawbytes()

        broadcast_msg_v1_bytes = bloxroute_version_manager.convert_message_first_bytes_to_older_version(1,
                                                                                                        BloxrouteMessageType.BROADCAST,
                                                                                                        broadcast_msg_bytes)

        broadcast_msg_v1 = bloxroute_message_factory_v1.create_message_from_buffer(broadcast_msg_v1_bytes)
        self.assertIsInstance(broadcast_msg_v1, BroadcastMessageV1)

        self.assertEqual(broadcast_msg_v1.msg_hash(), broadcast_msg.msg_hash())
        self.assertEqual(broadcast_msg_v1.blob(), broadcast_msg.blob())
        self.assertNotEqual(len(broadcast_msg_v1.rawbytes()), len(broadcast_msg.rawbytes()))

        self.assertEqual(random_hash, broadcast_msg_v1.msg_hash())
        self.assertEqual(random_blob_bytes, broadcast_msg_v1.blob())

    def test_convert_first_bytes_from_older_version__broadcast_message_v1(self):
        random_hash_bytes = helpers.generate_bytearray(SHA256_HASH_LEN)
        random_hash = ObjectHash(random_hash_bytes)
        random_blob_bytes = helpers.generate_bytearray(12345)
        broadcast_msg_v1 = BroadcastMessageV1(msg_hash=random_hash, blob=random_blob_bytes)
        broadcast_msg_v1_bytes = broadcast_msg_v1.rawbytes()

        broadcast_msg_bytes = bloxroute_version_manager.convert_message_first_bytes_from_older_version(1,
                                                                                                       BloxrouteMessageType.BROADCAST,
                                                                                                       broadcast_msg_v1_bytes)

        broadcast_msg = bloxroute_message_factory.create_message_from_buffer(broadcast_msg_bytes)
        self.assertIsInstance(broadcast_msg, BroadcastMessage)

        self.assertEqual(broadcast_msg.msg_hash(), broadcast_msg_v1.msg_hash())
        self.assertEqual(broadcast_msg.blob(), broadcast_msg_v1.blob())

        self.assertEqual(random_hash, broadcast_msg.msg_hash())
        self.assertEqual(random_blob_bytes, broadcast_msg.blob())
        self.assertEqual(DEFAULT_NETWORK_NUM, broadcast_msg.network_num())

    def test_convert_message_from_older_version__not_changed_messages(self):
        self._test_message_does_not_change(AckMessage)
        self._test_message_does_not_change(GetTxsMessage, [])
        self._test_message_does_not_change(TxsMessage, [])
        self._test_message_does_not_change(PingMessage)
        self._test_message_does_not_change(PongMessage)

    def test_size_change(self):
        self.assertEqual(-NETWORK_NUM_LEN,
                         bloxroute_version_manager.get_message_size_change_to_older_version(1,
                                                                                            BloxrouteMessageType.BROADCAST))
        self.assertEqual(NETWORK_NUM_LEN,
                         bloxroute_version_manager.get_message_size_change_from_older_version(1,
                                                                                              BloxrouteMessageType.BROADCAST))

    def _test_message_does_not_change(self, cls, *args):
        message = cls(*args)
        message_v1 = bloxroute_version_manager.convert_message_to_older_version(1, message)
        self.assertIsInstance(message_v1, cls)
        self.assertEqual(message, message_v1)

        message_v1 = cls(*args)
        message = bloxroute_version_manager.convert_message_from_older_version(1, message_v1)
        self.assertIsInstance(message, cls)
        self.assertEqual(message, message_v1)
