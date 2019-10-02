from bxcommon import constants
from bxcommon.constants import EMPTY_SOURCE_ID
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.messages.bloxroute.ack_message import AckMessage
from bxcommon.messages.bloxroute.block_holding_message import BlockHoldingMessage
from bxcommon.messages.bloxroute.bloxroute_version_manager import bloxroute_version_manager
from bxcommon.messages.bloxroute.broadcast_message import BroadcastMessage
from bxcommon.messages.bloxroute.get_txs_message import GetTxsMessage
from bxcommon.messages.bloxroute.hello_message import HelloMessage
from bxcommon.messages.bloxroute.key_message import KeyMessage
from bxcommon.messages.bloxroute.ping_message import PingMessage
from bxcommon.messages.bloxroute.pong_message import PongMessage
from bxcommon.messages.bloxroute.tx_message import TxMessage
from bxcommon.messages.bloxroute.txs_message import TxsMessage
from bxcommon.messages.bloxroute.v4.ack_message_v4 import AckMessageV4
from bxcommon.messages.bloxroute.v4.block_holding_message_v4 import BlockHoldingMessageV4
from bxcommon.messages.bloxroute.v4.broadcast_message_v4 import BroadcastMessageV4
from bxcommon.messages.bloxroute.v4.get_txs_message_v4 import GetTxsMessageV4
from bxcommon.messages.bloxroute.v4.hello_message_v4 import HelloMessageV4
from bxcommon.messages.bloxroute.v4.key_message_v4 import KeyMessageV4
from bxcommon.messages.bloxroute.v4.message_v4 import MessageV4
from bxcommon.messages.bloxroute.v4.ping_message_v4 import PingMessageV4
from bxcommon.messages.bloxroute.v4.pong_message_v4 import PongMessageV4
from bxcommon.messages.bloxroute.v4.tx_message_v4 import TxMessageV4
from bxcommon.messages.bloxroute.v4.txs_message_v4 import TxsMessageV4
from bxcommon.messages.bloxroute.v5.broadcast_message_converter_v5 import broadcast_message_converter_v5
from bxcommon.models.transaction_info import TransactionInfo
from bxcommon.test_utils import helpers
from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.utils import crypto, uuid_pack
from bxcommon.utils.crypto import SHA256_HASH_LEN
from bxcommon.utils.object_hash import Sha256Hash

NEW_VERSION_SOURCE_ID = uuid_pack.from_bytes(b"\x01" * 16)
EMPTY_SOURCE_ID_STR = EMPTY_SOURCE_ID.decode()


def _get_random_hash():
    random_hash_bytes = helpers.generate_bytearray(SHA256_HASH_LEN)

    return Sha256Hash(random_hash_bytes)


class BloxrouteVersionManagerV4Test(AbstractTestCase):

    def test_hello_message(self):
        self._test_to_old_version(HelloMessage(protocol_version=bloxroute_version_manager.CURRENT_PROTOCOL_VERSION,
                                               network_num=constants.DEFAULT_NETWORK_NUM))

        old_version_msg = HelloMessageV4(
            protocol_version=bloxroute_version_manager.CURRENT_PROTOCOL_VERSION,
            network_num=constants.DEFAULT_NETWORK_NUM)
        new_version_msg = bloxroute_version_manager.convert_message_from_older_version(4, old_version_msg)
        self.assertEqual(len(old_version_msg.rawbytes()), len(new_version_msg.rawbytes()[
                                                              constants.STARTING_SEQUENCE_BYTES_LEN:-constants.CONTROL_FLAGS_LEN]))
        self.assertEqual(new_version_msg.rawbytes()[:constants.STARTING_SEQUENCE_BYTES_LEN].tobytes(),
                         constants.STARTING_SEQUENCE_BYTES)
        self.assertEqual(1, new_version_msg.rawbytes()[-1])

    def test_ack_message(self):
        self._test_to_old_version(AckMessage())
        self._test_to_new_version(AckMessageV4())

    def test_ping_message(self):
        self._test_to_old_version(PingMessage(nonce=12345))
        self._test_to_new_version(PingMessageV4(nonce=12345))

    def test_pong_message(self):
        self._test_to_old_version(PongMessage(nonce=12345))
        self._test_to_new_version(PongMessageV4(nonce=12345))

    def test_tx_message(self):
        tx_hash = Sha256Hash(helpers.generate_bytes(crypto.SHA256_HASH_LEN))
        tx_contents = helpers.generate_bytes(250)
        network_num = 1234
        self._test_to_old_version_broadcast_message(TxMessage(message_hash=tx_hash, network_num=network_num,
                                                              source_id=NEW_VERSION_SOURCE_ID, tx_val=tx_contents))
        self._test_to_new_version_broadcast_message(TxMessageV4(tx_hash=tx_hash, network_num=network_num,
                                                                tx_val=tx_contents))

    def test_broadcast_message(self):
        block_hash = Sha256Hash(helpers.generate_bytes(crypto.SHA256_HASH_LEN))
        blob = helpers.generate_bytes(250)
        network_num = 1234
        self._test_to_old_version_broadcast_message(BroadcastMessage(network_num=network_num, message_hash=block_hash,
                                                                     source_id=NEW_VERSION_SOURCE_ID, blob=blob))
        self._test_to_new_version_broadcast_message(BroadcastMessageV4(network_num=network_num, msg_hash=block_hash,
                                                                       blob=blob))

    def test_broadcast_message_cut_through_to_old(self):
        block_hash = Sha256Hash(helpers.generate_bytes(crypto.SHA256_HASH_LEN))
        blob = helpers.generate_bytes(250)
        network_num = 1234
        new_message = BroadcastMessage(network_num=network_num, message_hash=block_hash, blob=blob)
        new_message_bytes = new_message.rawbytes()
        old_message_bytes = bloxroute_version_manager.convert_message_first_bytes_to_older_version(4,
                                                                                                   BroadcastMessageV4.MESSAGE_TYPE,
                                                                                                   new_message_bytes)
        old_message_bytes = bloxroute_version_manager.convert_message_last_bytes_to_older_version(4,
                                                                                                  BroadcastMessageV4.MESSAGE_TYPE,
                                                                                                  old_message_bytes)
        msg_type, payload_len = MessageV4.unpack(old_message_bytes)
        old_msg = MessageV4.initialize_class(BroadcastMessageV4, old_message_bytes, (msg_type, payload_len))
        self._validate_messages_match_broadcast_message(old_msg, new_message)

    def test_broadcast_message_cut_through_from_old(self):
        block_hash = Sha256Hash(helpers.generate_bytes(crypto.SHA256_HASH_LEN))
        blob = helpers.generate_bytes(250)
        network_num = 1234
        old_message = BroadcastMessageV4(network_num=network_num, msg_hash=block_hash, blob=blob)
        old_message_bytes = old_message.rawbytes()
        new_message_bytes = bloxroute_version_manager.convert_message_first_bytes_from_older_version(4,
                                                                                                     BroadcastMessage.MESSAGE_TYPE,
                                                                                                     old_message_bytes)
        new_message_bytes = bloxroute_version_manager.convert_message_last_bytes_from_older_version(4,
                                                                                                    BroadcastMessage.MESSAGE_TYPE,
                                                                                                    new_message_bytes)
        msg_type, payload_len = AbstractBloxrouteMessage.unpack(new_message_bytes)
        new_msg = AbstractBloxrouteMessage.initialize_class(
            BroadcastMessage,
            bytearray(new_message_bytes.tobytes()),
            (msg_type, payload_len)
        )
        self._validate_messages_match_broadcast_message(old_message, new_msg)
        self.assertEqual(EMPTY_SOURCE_ID_STR, new_msg.source_id())

    def test_get_txs_message(self):
        self._test_to_old_version(GetTxsMessage(short_ids=[1, 2, 3]))
        self._test_to_new_version(GetTxsMessageV4(short_ids=[1, 2, 3]))

    def test_txs_message(self):
        tx_hash = Sha256Hash(helpers.generate_bytes(crypto.SHA256_HASH_LEN))
        tx_contents = helpers.generate_bytes(250)
        self._test_to_old_version(TxsMessage([TransactionInfo(tx_hash, tx_contents, 1)]))
        self._test_to_new_version(TxsMessageV4([TransactionInfo(tx_hash, tx_contents, 1)]))

    def test_key_message(self):
        block_hash = Sha256Hash(helpers.generate_bytes(crypto.SHA256_HASH_LEN))
        network_num = 12345
        key = helpers.generate_bytes(crypto.KEY_SIZE)
        self._test_to_old_version_broadcast_message(KeyMessage(message_hash=block_hash, network_num=network_num,
                                                               source_id=NEW_VERSION_SOURCE_ID, key=key))
        self._test_to_new_version_broadcast_message(KeyMessageV4(msg_hash=block_hash, network_num=network_num, key=key))

    def test_block_hold_message(self):
        block_hash = Sha256Hash(helpers.generate_bytes(crypto.SHA256_HASH_LEN))
        network_num = 12345
        self._test_to_old_version_broadcast_message(BlockHoldingMessage(block_hash=block_hash, network_num=network_num,
                                                                        source_id=NEW_VERSION_SOURCE_ID))
        self._test_to_new_version_broadcast_message(BlockHoldingMessageV4(block_hash=block_hash,
                                                                          network_num=network_num))

    def _test_to_old_version(self, new_version_msg):
        old_version_msg = bloxroute_version_manager.convert_message_to_older_version(4, new_version_msg)
        self._validate_messages_match(old_version_msg, new_version_msg)

    def _test_to_new_version(self, old_version_msg):
        new_version_msg = bloxroute_version_manager.convert_message_from_older_version(4, old_version_msg)
        self._validate_messages_match(old_version_msg, new_version_msg)

    def _validate_messages_match(self, old_version_msg, new_version_msg):
        self.assertEqual(old_version_msg.payload(),
                         new_version_msg.payload()[:-constants.CONTROL_FLAGS_LEN])
        self.assertEqual(new_version_msg.rawbytes()[:constants.STARTING_SEQUENCE_BYTES_LEN].tobytes(),
                         constants.STARTING_SEQUENCE_BYTES)
        self.assertEqual(len(new_version_msg.rawbytes()), len(
            old_version_msg.rawbytes()) + constants.STARTING_SEQUENCE_BYTES_LEN + constants.CONTROL_FLAGS_LEN)
        self.assertEqual(1, new_version_msg.rawbytes()[-1])

    def _test_to_old_version_broadcast_message(self, new_version_msg):
        old_version_msg = bloxroute_version_manager.convert_message_to_older_version(4, new_version_msg)
        self._validate_messages_match_broadcast_message(old_version_msg, new_version_msg)

    def _test_to_new_version_broadcast_message(self, old_version_msg):
        new_version_msg = bloxroute_version_manager.convert_message_from_older_version(4, old_version_msg)
        self._validate_messages_match_broadcast_message(old_version_msg, new_version_msg)
        self.assertEqual(EMPTY_SOURCE_ID_STR, new_version_msg.source_id())

    def _validate_messages_match_broadcast_message(self, old_version_msg, new_version_msg):
        self.assertEqual(old_version_msg.msg_type(), new_version_msg.msg_type())
        self.assertEqual(old_version_msg.payload_len(),
                         new_version_msg.payload_len() - constants.NODE_ID_SIZE_IN_BYTES - constants.CONTROL_FLAGS_LEN)
        self.assertEqual(len(old_version_msg.rawbytes()),
                         len(new_version_msg.rawbytes()) - constants.NODE_ID_SIZE_IN_BYTES -
                         constants.CONTROL_FLAGS_LEN - constants.STARTING_SEQUENCE_BYTES_LEN)

        self.assertEqual(new_version_msg.rawbytes()[:constants.STARTING_SEQUENCE_BYTES_LEN].tobytes(),
                         constants.STARTING_SEQUENCE_BYTES)

        old_version_contents_part_1 = old_version_msg.rawbytes()[
                                      AbstractBloxrouteMessage.HEADER_LENGTH -
                                      constants.STARTING_SEQUENCE_BYTES_LEN:
                                      broadcast_message_converter_v5._LEFT_BREAKPOINT -
                                      constants.STARTING_SEQUENCE_BYTES_LEN
                                      ]
        new_versions_contents_part_1 = new_version_msg.rawbytes()[
                                       AbstractBloxrouteMessage.HEADER_LENGTH:
                                       broadcast_message_converter_v5._LEFT_BREAKPOINT
                                       ]
        self.assertEqual(old_version_contents_part_1, new_versions_contents_part_1)

        old_version_contents_part_2 = old_version_msg.rawbytes()[broadcast_message_converter_v5._LEFT_BREAKPOINT -
                                                                 constants.STARTING_SEQUENCE_BYTES_LEN:]
        new_versions_contents_part_2 = new_version_msg.rawbytes()[broadcast_message_converter_v5._RIGHT_BREAKPOINT:-1]
        self.assertEqual(old_version_contents_part_2, new_versions_contents_part_2)
