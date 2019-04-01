from bxcommon.messages.bloxroute.bloxroute_message_factory import bloxroute_message_factory
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.bloxroute_version_manager import bloxroute_version_manager
from bxcommon.messages.bloxroute.broadcast_message import BroadcastMessage
from bxcommon.messages.bloxroute.v3.bloxroute_message_factory_v3 import bloxroute_message_factory_v3
from bxcommon.messages.bloxroute.v3.broadcast_message_v3 import BroadcastMessageV3
from bxcommon.test_utils import helpers
from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.utils.crypto import SHA256_HASH_LEN
from bxcommon.utils.object_hash import Sha256Hash


def _get_random_hash():
    random_hash_bytes = helpers.generate_bytearray(SHA256_HASH_LEN)

    return Sha256Hash(random_hash_bytes)


class BloxrouteVersionManagerV3Test(AbstractTestCase):
    def test_convert_message_to_older_version__broadcast_message_v3(self):
        random_hash = _get_random_hash()
        random_blob_bytes = helpers.generate_bytearray(12345)
        broadcast_msg = BroadcastMessage(msg_hash=random_hash, network_num=1, is_encrypted=True, blob=random_blob_bytes)

        broadcast_msg_v3 = bloxroute_version_manager.convert_message_to_older_version(3, broadcast_msg)
        self.assertIsInstance(broadcast_msg_v3, BroadcastMessageV3)

        self.assertEqual(broadcast_msg_v3.block_hash(), broadcast_msg.block_hash())
        self.assertEqual(broadcast_msg_v3.network_num(), broadcast_msg.network_num())
        self.assertEqual(broadcast_msg_v3.blob(), broadcast_msg.blob())
        self.assertNotEqual(len(broadcast_msg_v3.rawbytes()), len(broadcast_msg.rawbytes()))

        self.assertEqual(random_hash, broadcast_msg_v3.block_hash())
        self.assertEqual(random_blob_bytes, broadcast_msg_v3.blob())

    def test_convert_message_from_older_version__broadcast_message_v3(self):
        random_hash_bytes = helpers.generate_bytearray(SHA256_HASH_LEN)
        random_hash = Sha256Hash(random_hash_bytes)
        random_blob_bytes = helpers.generate_bytearray(12345)
        broadcast_msg_v3 = BroadcastMessageV3(msg_hash=random_hash, network_num=12345, blob=random_blob_bytes)

        broadcast_msg = bloxroute_version_manager.convert_message_from_older_version(3, broadcast_msg_v3)
        self.assertIsInstance(broadcast_msg, BroadcastMessage)

        self.assertEqual(broadcast_msg.block_hash(), broadcast_msg_v3.block_hash())
        self.assertEqual(broadcast_msg.network_num(), broadcast_msg_v3.network_num())
        self.assertEqual(broadcast_msg.blob(), broadcast_msg_v3.blob())

        self.assertEqual(random_hash, broadcast_msg.block_hash())
        self.assertEqual(random_blob_bytes, broadcast_msg.blob())
        self.assertTrue(broadcast_msg.is_encrypted())

    def test_convert_first_bytes__to_older_version__broadcast_message_v3(self):
        random_hash = _get_random_hash()
        random_blob_bytes = helpers.generate_bytearray(12345)
        broadcast_msg = BroadcastMessage(msg_hash=random_hash, network_num=1, is_encrypted=True, blob=random_blob_bytes)
        broadcast_msg_bytes = broadcast_msg.rawbytes()

        broadcast_msg_v3_bytes = bloxroute_version_manager.convert_message_first_bytes_to_older_version(3,
                                                                                                        BloxrouteMessageType.BROADCAST,
                                                                                                        broadcast_msg_bytes)

        broadcast_msg_v3 = bloxroute_message_factory_v3.create_message_from_buffer(broadcast_msg_v3_bytes)
        self.assertIsInstance(broadcast_msg_v3, BroadcastMessageV3)

        self.assertEqual(broadcast_msg_v3.block_hash(), broadcast_msg.block_hash())
        self.assertEqual(broadcast_msg_v3.network_num(), broadcast_msg.network_num())
        self.assertEqual(broadcast_msg_v3.blob(), broadcast_msg.blob())
        self.assertNotEqual(len(broadcast_msg_v3.rawbytes()), len(broadcast_msg.rawbytes()))

        self.assertEqual(random_hash, broadcast_msg_v3.block_hash())
        self.assertEqual(random_blob_bytes, broadcast_msg_v3.blob())

    def test_convert_first_bytes_from_older_version__broadcast_message_v3(self):
        random_hash_bytes = helpers.generate_bytearray(SHA256_HASH_LEN)
        random_hash = Sha256Hash(random_hash_bytes)
        random_blob_bytes = helpers.generate_bytearray(12345)
        broadcast_msg_v3 = BroadcastMessageV3(msg_hash=random_hash, network_num=12345, blob=random_blob_bytes)
        broadcast_msg_v3_bytes = broadcast_msg_v3.rawbytes()

        broadcast_msg_bytes = bloxroute_version_manager.convert_message_first_bytes_from_older_version(3,
                                                                                                       BloxrouteMessageType.BROADCAST,
                                                                                                       broadcast_msg_v3_bytes)

        broadcast_msg = bloxroute_message_factory.create_message_from_buffer(broadcast_msg_bytes)
        self.assertIsInstance(broadcast_msg, BroadcastMessage)

        self.assertEqual(broadcast_msg.block_hash(), broadcast_msg_v3.block_hash())
        self.assertEqual(broadcast_msg.blob(), broadcast_msg_v3.blob())
        self.assertEqual(broadcast_msg.network_num(), broadcast_msg_v3.network_num())

        self.assertEqual(random_hash, broadcast_msg.block_hash())
        self.assertEqual(random_blob_bytes, broadcast_msg.blob())
        self.assertTrue(broadcast_msg.is_encrypted())
