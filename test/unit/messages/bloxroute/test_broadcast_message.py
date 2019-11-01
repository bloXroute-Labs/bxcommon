from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.messages.bloxroute.broadcast_message import BroadcastMessage
from bxcommon.test_utils import helpers
from bxcommon.utils.buffers.input_buffer import InputBuffer
from bxcommon.utils.crypto import SHA256_HASH_LEN
from bxcommon.utils.object_hash import Sha256Hash


class BroadcastMessageTest(AbstractTestCase):

    def test_peek_network_num(self):
        network_num = 12345
        hash_bytes = helpers.generate_bytearray(SHA256_HASH_LEN)
        msg_hash = Sha256Hash(hash_bytes)
        block_bytes = helpers.generate_bytearray(1234)

        broadcast_msg = BroadcastMessage(message_hash=msg_hash, network_num=network_num, source_id="", blob=block_bytes)

        msg_bytes = broadcast_msg.rawbytes()
        input_buffer = InputBuffer()
        input_buffer.add_bytes(msg_bytes)

        peeked_network_num = BroadcastMessage.peek_network_num(input_buffer)

        self.assertEqual(network_num, peeked_network_num)
