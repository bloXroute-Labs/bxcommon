from bxcommon.constants import DEFAULT_NETWORK_NUM, NETWORK_NUM_LEN, VERSION_NUM_LEN, NODE_ID_SIZE_IN_BYTES, \
    UL_INT_SIZE_IN_BYTES, BLOCK_ENCRYPTED_FLAG_LEN
from bxcommon.messages.bloxroute.ack_message import AckMessage
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.bloxroute_version_manager import bloxroute_version_manager
from bxcommon.messages.bloxroute.get_txs_message import GetTxsMessage
from bxcommon.messages.bloxroute.hello_message import HelloMessage
from bxcommon.messages.bloxroute.ping_message import PingMessage
from bxcommon.messages.bloxroute.txs_message import TxsMessage
from bxcommon.messages.bloxroute.v1.hello_message_v1 import HelloMessageV1
from bxcommon.messages.bloxroute.v1.ping_message_v1 import PingMessageV1
from bxcommon.messages.bloxroute.v2.hello_message_v2 import HelloMessageV2
from bxcommon.test_utils import helpers
from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.utils.buffers.input_buffer import InputBuffer
from bxcommon.utils.crypto import SHA256_HASH_LEN
from bxcommon.utils.object_hash import Sha256Hash


def _get_random_hash():
    random_hash_bytes = helpers.generate_bytearray(SHA256_HASH_LEN)

    return Sha256Hash(random_hash_bytes)


class BloxrouteVersionManagerV1Test(AbstractTestCase):

    def test_get_connection_protocol_version_v1(self):
        hello_msg_v1 = HelloMessageV1(idx=0)
        input_buffer = InputBuffer()
        input_buffer.add_bytes(hello_msg_v1.rawbytes())

        self.assertEqual(1, bloxroute_version_manager.get_connection_protocol_version(input_buffer))

    def test_get_connection_protocol_version_v2(self):
        hello_msg_v2 = HelloMessageV2(2, 0, 1)
        input_buffer = InputBuffer()
        input_buffer.add_bytes(hello_msg_v2.rawbytes())

        self.assertEqual(2, bloxroute_version_manager.get_connection_protocol_version(input_buffer))

    def test_convert_message_to_older_version__hello_message_v2(self):
        dummy_idx = 11

        hello_msg = HelloMessage(protocol_version=bloxroute_version_manager.CURRENT_PROTOCOL_VERSION,
                                 network_num=DEFAULT_NETWORK_NUM,
                                 node_id="c2b04fd2-7c81-432b-99a5-8b68f43d97e8")
        hello_msg_v1 = bloxroute_version_manager.convert_message_to_older_version(1, hello_msg)
        self.assertIsInstance(hello_msg_v1, HelloMessageV1)

        self.assertEqual(len(hello_msg_v1.rawbytes()) + NETWORK_NUM_LEN + VERSION_NUM_LEN, len(hello_msg.rawbytes()))
        self.assertEqual(hello_msg_v1.payload_len() + NETWORK_NUM_LEN + VERSION_NUM_LEN, hello_msg.payload_len())
        self.assertEqual(0, hello_msg_v1.idx())

    def test_convert_message_to_older_version__hello_message_v2_v1(self):
        dummy_idx = 11

        hello_msg = HelloMessage(protocol_version=bloxroute_version_manager.CURRENT_PROTOCOL_VERSION,
                                 network_num=DEFAULT_NETWORK_NUM,
                                 node_id="c2b04fd2-7c81-432b-99a5-8b68f43d97e8")
        hello_msg_v2 = bloxroute_version_manager.convert_message_to_older_version(2, hello_msg)
        self.assertIsInstance(hello_msg_v2, HelloMessageV2)
        self.assertEqual(len(hello_msg_v2.rawbytes()) + hello_msg.HELLO_MESSAGE_BLOCK.size - UL_INT_SIZE_IN_BYTES,
                         len(hello_msg.rawbytes()))
        self.assertEqual(hello_msg_v2.payload_len() + hello_msg.HELLO_MESSAGE_BLOCK.size - UL_INT_SIZE_IN_BYTES,
                         hello_msg.payload_len())
        self.assertEqual(0, hello_msg_v2.idx())

    def test_convert_message_from_older_version__hello_message_v2_v3(self):
        dummy_idx = 15

        hello_msg_v2 = HelloMessageV2(idx=dummy_idx, protocol_version=2, network_num=DEFAULT_NETWORK_NUM)
        hello_msg = bloxroute_version_manager.convert_message_from_older_version(2, hello_msg_v2)

        self.assertIsInstance(hello_msg, HelloMessage)
        self.assertEqual(len(hello_msg_v2.rawbytes()) + NODE_ID_SIZE_IN_BYTES - UL_INT_SIZE_IN_BYTES,
                         len(hello_msg.rawbytes()))
        self.assertEqual(hello_msg_v2.payload_len() + NODE_ID_SIZE_IN_BYTES - UL_INT_SIZE_IN_BYTES,
                         hello_msg.payload_len())

        self.assertEqual(2, hello_msg.protocol_version())
        self.assertEqual(DEFAULT_NETWORK_NUM, hello_msg.network_num())

    def test_convert_message_from_older_version__ping_message_v0_v3(self):
        nonce = 15
        ping_v0 = PingMessageV1()
        ping = bloxroute_version_manager.convert_message_from_older_version(2, ping_v0)
        self.assertIsInstance(ping, PingMessage)
        self.assertEqual(len(ping_v0.rawbytes()) + 8, len(ping.rawbytes()))

    def test_convert_message_from_older_version__not_changed_messages(self):
        self._test_message_does_not_change(AckMessage)
        self._test_message_does_not_change(GetTxsMessage, [])
        self._test_message_does_not_change(TxsMessage, [])

    def test_size_change(self):
        self.assertEqual(- NETWORK_NUM_LEN - BLOCK_ENCRYPTED_FLAG_LEN,
                         bloxroute_version_manager.get_message_size_change_to_older_version(1,
                                                                                            BloxrouteMessageType.BROADCAST))
        self.assertEqual(NETWORK_NUM_LEN + BLOCK_ENCRYPTED_FLAG_LEN,
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
