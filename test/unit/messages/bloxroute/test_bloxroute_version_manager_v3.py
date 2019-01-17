from bxcommon.constants import DEFAULT_NETWORK_NUM, NETWORK_NUM_LEN, VERSION_NUM_LEN, NODE_ID_SIZE_IN_BYTES
from bxcommon.messages.bloxroute.ack_message import AckMessage
from bxcommon.messages.bloxroute.bloxroute_message_factory import bloxroute_message_factory
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.bloxroute_version_manager import bloxroute_version_manager
from bxcommon.messages.bloxroute.broadcast_message import BroadcastMessage
from bxcommon.messages.bloxroute.get_txs_message import GetTxsMessage
from bxcommon.messages.bloxroute.hello_message import HelloMessage
from bxcommon.messages.bloxroute.key_message import KeyMessage
from bxcommon.messages.bloxroute.ping_message import PingMessage
from bxcommon.messages.bloxroute.v1.ping_message_v1 import PingMessageV1
from bxcommon.messages.bloxroute.v1.keep_alive_message_v1 import KeepAliveMessageV1
from bxcommon.messages.bloxroute.pong_message import PongMessage
from bxcommon.messages.bloxroute.tx_message import TxMessage
from bxcommon.messages.bloxroute.txs_message import TxsMessage
from bxcommon.messages.bloxroute.v1.bloxroute_message_factory_v1 import bloxroute_message_factory_v1
from bxcommon.messages.bloxroute.v1.broadcast_message_v1 import BroadcastMessageV1
from bxcommon.messages.bloxroute.v1.hello_message_v1 import HelloMessageV1
from bxcommon.messages.bloxroute.v2.hello_message_v2 import HelloMessageV2
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


class BloxrouteVersionManagerV3Test(AbstractTestCase):

    def test_convert_message_to_older_version__ping_message_v3(self):
        nonce = 50
        ping_msg = PingMessage(nonce=nonce)
        ping_msg_v1 = bloxroute_version_manager.convert_message_to_older_version(1, ping_msg)
        self.assertIsInstance(ping_msg_v1, PingMessageV1)
        self.assertEqual(len(ping_msg_v1.rawbytes()) + PingMessage.KEEP_ALIVE_MESSAGE_LENGTH, len(ping_msg.rawbytes()))
        self.assertEqual(ping_msg_v1.payload_len() + PingMessage.KEEP_ALIVE_MESSAGE_LENGTH , ping_msg.payload_len())

    def test_convert_message_from_older_version__ping_message_v1_v3(self):
        ping_msg_v1 = PingMessageV1()
        ping_msg = bloxroute_version_manager.convert_message_from_older_version(1, ping_msg_v1)
        self.assertIsNone(ping_msg.nonce())
        self.assertEqual(ping_msg_v1.payload_len() + PingMessage.KEEP_ALIVE_MESSAGE_LENGTH, ping_msg.payload_len())
