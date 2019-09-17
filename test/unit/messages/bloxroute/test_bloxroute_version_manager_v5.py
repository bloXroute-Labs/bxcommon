from bxcommon import constants
from bxcommon.constants import EMPTY_SOURCE_ID
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.messages.bloxroute.abstract_broadcast_message import AbstractBroadcastMessage
from bxcommon.messages.bloxroute.block_holding_message import BlockHoldingMessage
from bxcommon.messages.bloxroute.bloxroute_version_manager import bloxroute_version_manager
from bxcommon.messages.bloxroute.broadcast_message import BroadcastMessage
from bxcommon.messages.bloxroute.key_message import KeyMessage
from bxcommon.messages.bloxroute.tx_message import TxMessage
from bxcommon.messages.bloxroute.v5.block_holding_message_v5 import BlockHoldingMessageV5
from bxcommon.messages.bloxroute.v5.broadcast_message_converter_v5 import broadcast_message_converter_v5
from bxcommon.messages.bloxroute.v5.broadcast_message_v5 import BroadcastMessageV5
from bxcommon.messages.bloxroute.v5.key_message_v5 import KeyMessageV5
from bxcommon.messages.bloxroute.v5.tx_message_v5 import TxMessageV5
from bxcommon.test_utils import helpers
from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.utils import crypto, uuid_pack
from bxcommon.utils.object_hash import Sha256Hash

NEW_VERSION_SOURCE_ID = uuid_pack.from_bytes(b"\x01" * 16)


class BloxrouteVersionManagerV5Test(AbstractTestCase):

    def test_tx_message(self):
        tx_hash = Sha256Hash(helpers.generate_bytes(crypto.SHA256_HASH_LEN))
        tx_contents = helpers.generate_bytes(250)
        network_num = 1234
        self._test_to_old_version(TxMessage(message_hash=tx_hash, network_num=network_num,
                                            source_id=NEW_VERSION_SOURCE_ID, tx_val=tx_contents))
        self._test_to_new_version(TxMessageV5(tx_hash=tx_hash, network_num=network_num, tx_val=tx_contents))

    def test_broadcast_message(self):
        block_hash = Sha256Hash(helpers.generate_bytes(crypto.SHA256_HASH_LEN))
        blob = helpers.generate_bytes(250)
        network_num = 1234
        self._test_to_old_version(BroadcastMessage(network_num=network_num, message_hash=block_hash,
                                                   source_id=NEW_VERSION_SOURCE_ID, blob=blob))
        self._test_to_new_version(BroadcastMessageV5(network_num=network_num, msg_hash=block_hash, blob=blob))

    def test_broadcast_message_cut_through_to_old(self):
        block_hash = Sha256Hash(helpers.generate_bytes(crypto.SHA256_HASH_LEN))
        blob = helpers.generate_bytes(250)
        network_num = 1234
        new_message = BroadcastMessage(network_num=network_num, message_hash=block_hash,
                                       source_id=NEW_VERSION_SOURCE_ID, blob=blob)
        new_message_bytes = new_message.rawbytes()
        old_message_bytes = bloxroute_version_manager.convert_message_first_bytes_to_older_version(
            5,
            BroadcastMessage.MESSAGE_TYPE,
            new_message_bytes
        )
        msg_type, payload_length = BroadcastMessageV5.unpack(old_message_bytes)
        old_msg = BroadcastMessageV5.initialize_class(
            BroadcastMessageV5,
            old_message_bytes,
            (msg_type, payload_length)
        )
        self._validate_messages_match(old_msg, new_message)

    def test_broadcast_message_cut_through_from_old(self):
        block_hash = Sha256Hash(helpers.generate_bytes(crypto.SHA256_HASH_LEN))
        blob = helpers.generate_bytes(250)
        network_num = 1234
        old_message = BroadcastMessageV5(network_num=network_num, msg_hash=block_hash, blob=blob)
        old_message_bytes = old_message.rawbytes()
        new_message_bytes = bloxroute_version_manager.convert_message_first_bytes_from_older_version(
            5,
            BroadcastMessage.MESSAGE_TYPE,
            old_message_bytes
        )
        new_message_bytes = bloxroute_version_manager.convert_message_last_bytes_from_older_version(
            5,
            BroadcastMessage.MESSAGE_TYPE,
            new_message_bytes
        )
        msg_type, payload_length = AbstractBloxrouteMessage.unpack(new_message_bytes)
        new_msg = AbstractBloxrouteMessage.initialize_class(
            BroadcastMessage,
            bytearray(new_message_bytes.tobytes()),
            (msg_type, payload_length)
        )
        self._validate_messages_match(old_message, new_msg)
        self.assertEqual(EMPTY_SOURCE_ID, new_msg.source_id())

    def test_key_message(self):
        block_hash = Sha256Hash(helpers.generate_bytes(crypto.SHA256_HASH_LEN))
        network_num = 12345
        key = helpers.generate_bytes(crypto.KEY_SIZE)
        self._test_to_old_version(KeyMessage(message_hash=block_hash, network_num=network_num,
                                             source_id=NEW_VERSION_SOURCE_ID, key=key))
        self._test_to_new_version(KeyMessageV5(msg_hash=block_hash, network_num=network_num, key=key))

    def test_block_hold_message(self):
        block_hash = Sha256Hash(helpers.generate_bytes(crypto.SHA256_HASH_LEN))
        network_num = 12345
        self._test_to_old_version(BlockHoldingMessage(block_hash=block_hash, network_num=network_num,
                                                      source_id=NEW_VERSION_SOURCE_ID))
        self._test_to_new_version(BlockHoldingMessageV5(block_hash=block_hash, network_num=network_num))

    def _test_to_old_version(self, new_version_msg: AbstractBroadcastMessage):
        old_version_msg = bloxroute_version_manager.convert_message_to_older_version(5, new_version_msg)
        self._validate_messages_match(old_version_msg, new_version_msg)

    def _test_to_new_version(self, old_version_msg: AbstractBloxrouteMessage):
        new_version_msg: AbstractBroadcastMessage = \
            bloxroute_version_manager.convert_message_from_older_version(5, old_version_msg)
        self._validate_messages_match(old_version_msg, new_version_msg)
        self.assertEqual(EMPTY_SOURCE_ID, new_version_msg.source_id())

    def _validate_messages_match(self, old_version_msg, new_version_msg):
        self.assertEqual(old_version_msg.msg_type(), new_version_msg.msg_type())
        self.assertEqual(old_version_msg.payload_len(), new_version_msg.payload_len() - constants.NODE_ID_SIZE_IN_BYTES)
        self.assertEqual(old_version_msg.rawbytes()[
                         AbstractBloxrouteMessage.HEADER_LENGTH:broadcast_message_converter_v5._LEFT_BREAKPOINT],
                         new_version_msg.rawbytes()[
                         AbstractBloxrouteMessage.HEADER_LENGTH:broadcast_message_converter_v5._LEFT_BREAKPOINT])
        self.assertEqual(old_version_msg.rawbytes()[broadcast_message_converter_v5._LEFT_BREAKPOINT:],
                         new_version_msg.rawbytes()[broadcast_message_converter_v5._RIGHT_BREAKPOINT:])
