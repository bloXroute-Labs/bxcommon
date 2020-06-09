import random
import struct
import time
from typing import TypeVar, Type
from datetime import datetime

from bxcommon import constants
from bxcommon.constants import UL_INT_SIZE_IN_BYTES, NETWORK_NUM_LEN, \
    NODE_ID_SIZE_IN_BYTES, \
    BX_HDR_COMMON_OFF, BLOCK_ENCRYPTED_FLAG_LEN, QUOTA_FLAG_LEN, BROADCAST_TYPE_LEN
from bxcommon.exceptions import PayloadLenError
from bxcommon.messages.bloxroute.abstract_broadcast_message import \
    AbstractBroadcastMessage
from bxcommon.messages.bloxroute.ack_message import AckMessage
from bxcommon.messages.bloxroute.bdn_performance_stats_message import BdnPerformanceStatsMessage
from bxcommon.messages.bloxroute.block_confirmation_message import \
    BlockConfirmationMessage
from bxcommon.messages.bloxroute.block_holding_message import \
    BlockHoldingMessage
from bxcommon.messages.bloxroute.bloxroute_message_factory import \
    bloxroute_message_factory
from bxcommon.messages.bloxroute.bloxroute_version_manager import \
    bloxroute_version_manager
from bxcommon.messages.bloxroute.broadcast_message import BroadcastMessage
from bxcommon.messages.bloxroute.get_tx_contents_message import GetTxContentsMessage
from bxcommon.messages.bloxroute.get_txs_message import GetTxsMessage
from bxcommon.messages.bloxroute.hello_message import HelloMessage
from bxcommon.messages.bloxroute.key_message import KeyMessage
from bxcommon.messages.bloxroute.notification_message import \
    NotificationMessage, NotificationCode
from bxcommon.messages.bloxroute.ping_message import PingMessage
from bxcommon.messages.bloxroute.pong_message import PongMessage
from bxcommon.messages.bloxroute.transaction_cleanup_message import \
    TransactionCleanupMessage
from bxcommon.messages.bloxroute.tx_contents_message import TxContentsMessage
from bxcommon.messages.bloxroute.tx_message import TxMessage
from bxcommon.messages.bloxroute.txs_message import TxsMessage
from bxcommon.messages.bloxroute.version_message import VersionMessage
from bxcommon.models.broadcast_message_type import BroadcastMessageType
from bxcommon.models.entity_type_model import EntityType
from bxcommon.models.quota_type_model import QuotaType
from bxcommon.models.transaction_info import TransactionInfo
from bxcommon.test_utils import helpers
from bxcommon.test_utils.helpers import create_input_buffer_with_bytes
from bxcommon.test_utils.message_factory_test_case import MessageFactoryTestCase
from bxcommon.utils import crypto
from bxcommon.utils.crypto import SHA256_HASH_LEN, KEY_SIZE
from bxcommon.utils.object_hash import Sha256Hash, NULL_SHA256_HASH, ConcatHash

T = TypeVar("T")


class BloxrouteMessageFactory(MessageFactoryTestCase):
    HASH = Sha256Hash(crypto.double_sha256(b"123"))
    NETWORK_NUM = 12345
    NETWORK_NUM_BYTEARRAY = bytearray(constants.NETWORK_NUM_LEN)
    struct.pack_into("<L", NETWORK_NUM_BYTEARRAY, 0, NETWORK_NUM)
    NODE_ID = "c2b04fd2-7c81-432b-99a5-8b68f43d97e8"
    BROADCAST_TYPE = BroadcastMessageType.BLOCK
    MESSAGE_ID = ConcatHash(
        crypto.double_sha256(b"123") + NETWORK_NUM_BYTEARRAY +
        bytearray(BROADCAST_TYPE.value.encode(constants.DEFAULT_TEXT_ENCODING)), 0
    )

    def get_message_factory(self):
        return bloxroute_message_factory

    def create_message_successfully(
        self,
        message: T,
        message_type: Type[T],
    ) -> T:
        # check control flag
        result = super().create_message_successfully(message, message_type)
        self.assertEqual(1, result.rawbytes()[-1])
        self.assertEqual(len(message.rawbytes()) - message.HEADER_LENGTH, message.payload_len())
        return result

    def get_hashed_message_preview_successfully(self, message, expected_hash):
        is_full_message, block_hash, broadcast_type, msg_id, network_num, node_id, _payload_length = \
            bloxroute_message_factory.get_broadcast_message_preview(create_input_buffer_with_bytes(
                message.rawbytes()[:message.HEADER_LENGTH + SHA256_HASH_LEN + NETWORK_NUM_LEN + NODE_ID_SIZE_IN_BYTES +
                                    BROADCAST_TYPE_LEN]))
        self.assertTrue(is_full_message)
        self.assertEqual(expected_hash, block_hash)
        self.assertEqual(self.BROADCAST_TYPE, broadcast_type)
        self.assertEqual(self.MESSAGE_ID, msg_id)
        self.assertEqual(self.NODE_ID, node_id)
        self.assertEqual(self.NETWORK_NUM, network_num)

    def test_message_preview_success_all_types(self):
        self.get_message_preview_successfully(HelloMessage(protocol_version=1, network_num=2),
                                              HelloMessage.MESSAGE_TYPE,
                                              VersionMessage.VERSION_MESSAGE_LENGTH + UL_INT_SIZE_IN_BYTES +
                                              NODE_ID_SIZE_IN_BYTES - UL_INT_SIZE_IN_BYTES)
        self.get_message_preview_successfully(AckMessage(), AckMessage.MESSAGE_TYPE, constants.CONTROL_FLAGS_LEN)
        self.get_message_preview_successfully(PingMessage(), PingMessage.MESSAGE_TYPE, 9)
        self.get_message_preview_successfully(PongMessage(), PongMessage.MESSAGE_TYPE, 9)

        blob = bytearray(1 for _ in range(4))
        self.get_message_preview_successfully(BroadcastMessage(self.HASH, 1, self.NODE_ID, self.BROADCAST_TYPE, True,
                                                               blob),
                                              BroadcastMessage.MESSAGE_TYPE,
                                              SHA256_HASH_LEN + NETWORK_NUM_LEN + constants.BROADCAST_TYPE_LEN +
                                              BLOCK_ENCRYPTED_FLAG_LEN + constants.NODE_ID_SIZE_IN_BYTES + len(blob) +
                                              constants.CONTROL_FLAGS_LEN)
        self.get_message_preview_successfully(TxMessage(self.HASH, 1, self.NODE_ID, 12, blob),
                                              TxMessage.MESSAGE_TYPE,
                                              SHA256_HASH_LEN + NETWORK_NUM_LEN + UL_INT_SIZE_IN_BYTES +
                                              QUOTA_FLAG_LEN + constants.NODE_ID_SIZE_IN_BYTES + len(blob) +
                                              constants.UL_INT_SIZE_IN_BYTES +
                                              constants.CONTROL_FLAGS_LEN)
        self.get_message_preview_successfully(KeyMessage(self.HASH, 1, self.NODE_ID,
                                                         bytearray(1 for _ in range(KEY_SIZE))),
                                              KeyMessage.MESSAGE_TYPE,
                                              SHA256_HASH_LEN + KEY_SIZE + NETWORK_NUM_LEN +
                                              constants.NODE_ID_SIZE_IN_BYTES + constants.CONTROL_FLAGS_LEN)
        self.get_message_preview_successfully(BlockHoldingMessage(self.HASH, 1, self.NODE_ID),
                                              BlockHoldingMessage.MESSAGE_TYPE,
                                              SHA256_HASH_LEN + NETWORK_NUM_LEN + constants.NODE_ID_SIZE_IN_BYTES +
                                              constants.CONTROL_FLAGS_LEN)

        get_txs = [1, 2, 3]
        self.get_message_preview_successfully(GetTxsMessage(get_txs), GetTxsMessage.MESSAGE_TYPE,
                                              UL_INT_SIZE_IN_BYTES + UL_INT_SIZE_IN_BYTES * len(
                                                  get_txs) + constants.CONTROL_FLAGS_LEN)

        txs = [TransactionInfo(crypto.double_sha256(b"123"), bytearray(4), 1),
               TransactionInfo(crypto.double_sha256(b"234"), bytearray(8), 2)]
        expected_length = (UL_INT_SIZE_IN_BYTES +
                           sum(UL_INT_SIZE_IN_BYTES + SHA256_HASH_LEN + UL_INT_SIZE_IN_BYTES +
                               len(tx.contents) for tx in txs) + constants.CONTROL_FLAGS_LEN)
        self.get_message_preview_successfully(TxsMessage(txs), TxsMessage.MESSAGE_TYPE, expected_length)

        expected_length = (2 * constants.DOUBLE_SIZE_IN_BYTES) + (2 * constants.UL_SHORT_SIZE_IN_BYTES) + \
                          (2 * constants.UL_INT_SIZE_IN_BYTES) + constants.CONTROL_FLAGS_LEN
        self.get_message_preview_successfully(
            BdnPerformanceStatsMessage(datetime.utcnow(), datetime.utcnow(), 100, 200, 300, 400),
            BdnPerformanceStatsMessage.MESSAGE_TYPE,
            expected_length
        )

        tx_info = TransactionInfo(crypto.double_sha256(b"123"), bytearray(4), 1)
        expected_length = constants.NETWORK_NUM_LEN + constants.SID_LEN + SHA256_HASH_LEN + \
                          constants.UL_INT_SIZE_IN_BYTES + constants.CONTROL_FLAGS_LEN + len(tx_info.contents)
        self.get_message_preview_successfully(TxContentsMessage(5, tx_info),
                                              TxContentsMessage.MESSAGE_TYPE,
                                              expected_length)

        expected_length = constants.NETWORK_NUM_LEN + constants.SID_LEN + constants.CONTROL_FLAGS_LEN
        self.get_message_preview_successfully(GetTxContentsMessage(1, 2),
                                              GetTxContentsMessage.MESSAGE_TYPE,
                                              expected_length)

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
        self.get_hashed_message_preview_successfully(BroadcastMessage(self.HASH, self.NETWORK_NUM, self.NODE_ID,
                                                                      self.BROADCAST_TYPE, True, blob),
                                                     self.HASH)

    def test_message_hash_preview_incomplete(self):
        blob = bytearray(1 for _ in range(4))
        broadcast_message = BroadcastMessage(self.HASH, 123, self.NODE_ID, self.BROADCAST_TYPE, True, blob)

        is_full_message, block_hash, broadcast_type, msg_id, network_num, node_id, payload_length = \
            bloxroute_message_factory.get_broadcast_message_preview(
                create_input_buffer_with_bytes(broadcast_message.rawbytes()
                                               [:BX_HDR_COMMON_OFF + SHA256_HASH_LEN + NETWORK_NUM_LEN - 1]))
        self.assertFalse(is_full_message)
        self.assertIsNone(block_hash)
        self.assertIsNone(broadcast_type)
        self.assertIsNone(msg_id)
        self.assertIsNone(network_num)
        self.assertIsNone(node_id)
        self.assertIsNone(payload_length)

    def test_create_message_success_all_types(self):
        test_network_num = 10
        test_protocol_version = bloxroute_version_manager.CURRENT_PROTOCOL_VERSION

        hello_message = self.create_message_successfully(HelloMessage(protocol_version=test_protocol_version,
                                                                      network_num=test_network_num,
                                                                      node_id=self.NODE_ID
                                                                      ),
                                                         HelloMessage)
        self.assertEqual(test_protocol_version, hello_message.protocol_version())
        self.assertEqual(test_network_num, hello_message.network_num())
        self.assertEqual(self.NODE_ID, hello_message.node_id())
        self.create_message_successfully(AckMessage(), AckMessage)
        self.create_message_successfully(PingMessage(), PingMessage)
        self.create_message_successfully(PongMessage(), PongMessage)

        blob = bytearray(4)
        broadcast_message = self.create_message_successfully(BroadcastMessage(self.HASH,
                                                                              network_num=test_network_num,
                                                                              is_encrypted=True,
                                                                              source_id=self.NODE_ID,
                                                                              blob=blob),
                                                             BroadcastMessage)
        self.assertEqual(self.HASH, broadcast_message.block_hash())
        self.assertEqual(test_network_num, broadcast_message.network_num())
        self.assertEqual(self.NODE_ID, broadcast_message.source_id())
        self.assertTrue(broadcast_message.is_encrypted())
        self.assertEqual(blob, broadcast_message.blob().tobytes())

        sid = 12
        tx_val = bytes(1 for _ in range(5))
        tx_message = self.create_message_successfully(TxMessage(self.HASH,
                                                                network_num=test_network_num,
                                                                source_id=self.NODE_ID,
                                                                short_id=sid,
                                                                tx_val=tx_val),
                                                      TxMessage)
        self.assertEqual(self.HASH, tx_message.tx_hash())
        self.assertEqual(self.NODE_ID, tx_message.source_id())
        self.assertEqual(sid, tx_message.short_id())
        self.assertEqual(test_network_num, tx_message.network_num())
        self.assertEqual(tx_val, tx_message.tx_val())

        key = bytearray(1 for _ in range(KEY_SIZE))
        key_message = self.create_message_successfully(
            KeyMessage(self.HASH, test_network_num, self.NODE_ID, bytearray(1 for _ in range(KEY_SIZE))),
            KeyMessage
        )
        self.assertEqual(key, key_message.key())
        self.assertEqual(self.NODE_ID, key_message.source_id())
        self.assertEqual(test_network_num, key_message.network_num())
        self.assertEqual(self.HASH, key_message.block_hash())

        block_holding_message = self.create_message_successfully(
            BlockHoldingMessage(self.HASH, test_network_num, self.NODE_ID),
            BlockHoldingMessage
        )
        self.assertEqual(self.NODE_ID, block_holding_message.source_id())
        self.assertEqual(test_network_num, block_holding_message.network_num())
        self.assertEqual(self.HASH, block_holding_message.block_hash())

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

        get_tx_contents_message = self.create_message_successfully(GetTxContentsMessage(test_network_num, sid),
                                                                  GetTxContentsMessage)
        self.assertEqual(sid, get_tx_contents_message.get_short_id())
        self.assertEqual(test_network_num, get_tx_contents_message.network_num())

        tx_info = TransactionInfo(Sha256Hash(crypto.double_sha256(b"123")), bytearray(4), 1)
        tx_contents_message = self.create_message_successfully(TxContentsMessage(test_network_num, tx_info),
                                                              TxContentsMessage)
        self.assertEqual(test_network_num, tx_contents_message.network_num())
        result_tx_info = tx_contents_message.get_tx_info()
        self.assertEqual(tx_info.hash, result_tx_info.hash)
        self.assertEqual(tx_info.contents, result_tx_info.contents)
        self.assertEqual(tx_info.short_id, result_tx_info.short_id)

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

    def test_block_confirmation_msg(self):
        short_ids = [random.randint(0, 1000000) for _ in range(150)]
        tx_hashes = [
            Sha256Hash(helpers.generate_bytes(crypto.SHA256_HASH_LEN))
            for _ in range(10)
        ]
        message = BlockConfirmationMessage(self.HASH, self.NETWORK_NUM, self.NODE_ID, sids=short_ids,
                                           tx_hashes=tx_hashes)
        self.get_message_preview_successfully(message,
                                              BlockConfirmationMessage.MESSAGE_TYPE,
                                              SHA256_HASH_LEN * len(tx_hashes) +
                                              constants.UL_INT_SIZE_IN_BYTES * len(short_ids) +
                                              AbstractBroadcastMessage.PAYLOAD_LENGTH +
                                              constants.UL_INT_SIZE_IN_BYTES * 2)

        rebuilt_msg = self.create_message_successfully(message, BlockConfirmationMessage)
        self.assertEqual(self.HASH, rebuilt_msg.block_hash())
        self.assertEqual(short_ids, rebuilt_msg.short_ids())
        self.assertEqual(tx_hashes, rebuilt_msg.transaction_hashes())
        self.assertEqual(self.NETWORK_NUM, rebuilt_msg.network_num())
        self.assertEqual(self.NODE_ID, rebuilt_msg.source_id())

    def test_transaction_cleanup_msg(self):
        short_ids = [23, 99, 192, 1089, 3000500]
        tx_hashes = [
            Sha256Hash(helpers.generate_bytes(crypto.SHA256_HASH_LEN)),
            Sha256Hash(helpers.generate_bytes(crypto.SHA256_HASH_LEN))
        ]
        message = TransactionCleanupMessage(self.NETWORK_NUM, self.NODE_ID, sids=short_ids, tx_hashes=tx_hashes)
        self.get_message_preview_successfully(message,
                                              TransactionCleanupMessage.MESSAGE_TYPE,
                                              SHA256_HASH_LEN * len(tx_hashes) +
                                              constants.UL_INT_SIZE_IN_BYTES * len(short_ids) +
                                              AbstractBroadcastMessage.PAYLOAD_LENGTH +
                                              constants.UL_INT_SIZE_IN_BYTES * 2)

        rebuilt_msg = self.create_message_successfully(message, TransactionCleanupMessage)
        self.assertEqual(short_ids, rebuilt_msg.short_ids())
        self.assertEqual(tx_hashes, rebuilt_msg.transaction_hashes())
        self.assertEqual(self.NETWORK_NUM, rebuilt_msg.network_num())
        self.assertEqual(self.NODE_ID, rebuilt_msg.source_id())
        self.assertNotEqual(NULL_SHA256_HASH, rebuilt_msg.message_hash())

    def test_tx_bx_message(self):
        sid = 12
        tx_val = bytes(1 for _ in range(5))
        test_network_num = 4

        timestamp = time.time() - 4
        expected_tx_message = TxMessage(
            self.HASH,
            network_num=test_network_num,
            source_id=self.NODE_ID,
            short_id=sid,
            tx_val=tx_val,
            quota_type=QuotaType.PAID_DAILY_QUOTA,
            timestamp=timestamp
        )

        tx_message = self.create_message_successfully(
            expected_tx_message,
            TxMessage)
        self.assertEqual(self.HASH, tx_message.tx_hash())
        self.assertEqual(self.NODE_ID, tx_message.source_id())
        self.assertEqual(sid, tx_message.short_id())
        self.assertEqual(test_network_num, tx_message.network_num())
        self.assertEqual(tx_val, tx_message.tx_val())
        self.assertEqual(QuotaType.PAID_DAILY_QUOTA, tx_message.quota_type())
        self.assertEqual(int(timestamp), tx_message.timestamp())

        new_timestamp = time.time() - 2
        expected_tx_message.set_timestamp(new_timestamp)
        self.assertEqual(int(new_timestamp), expected_tx_message.timestamp())

        regenerated_tx_message = self.create_message_successfully(
            expected_tx_message,
            TxMessage
        )
        self.assertEqual(int(new_timestamp), regenerated_tx_message.timestamp())

    def test_tx_bx_message_setting_attributes(self):
        contents = helpers.generate_bytes(250)
        timestamp = time.time()
        tx_message = TxMessage(
            self.HASH,
            network_num=1,
            source_id=self.NODE_ID,
            short_id=2,
            tx_val=contents,
            quota_type=QuotaType.PAID_DAILY_QUOTA,
            timestamp=timestamp
        )
        tx_message.clear_protected_fields()

        rebuilt_tx_message = self.create_message_successfully(
            tx_message,
            TxMessage
        )
        self.assertEqual(constants.NULL_TX_SID, rebuilt_tx_message.short_id())
        self.assertEqual(constants.NULL_TX_TIMESTAMP, rebuilt_tx_message.timestamp())

    def test_notification_message(self):
        notification_code = NotificationCode.QUOTA_FILL_STATUS
        args_list = ["10", str(EntityType.TRANSACTION.value), "100"]
        raw_message = ",".join(args_list)

        notification_message = self.create_message_successfully(
            NotificationMessage(notification_code, raw_message),
            NotificationMessage)

        self.assertEqual(notification_code, notification_message.notification_code())
        self.assertEqual(raw_message, notification_message.raw_message())
        self.assertEqual(
            notification_message.formatted_message(),
            "10% of daily transaction quota with limit of 100 transactions per day is depleted."
        )

    def test_bdn_performance_stats_message(self):
        start_time = datetime.utcnow()
        new_blocks_received_from_blockchain_node = 100
        new_blocks_received_from_bdn = 200
        new_tx_received_from_blockchain_node = 300
        new_tx_received_from_bdn = 65535 + 1  # unsigned short max (0xffff) + 1
        end_time = datetime.utcnow()

        bdn_stats_msg = \
            self.create_message_successfully(BdnPerformanceStatsMessage(start_time,
                                                                        end_time,
                                                                        new_blocks_received_from_blockchain_node,
                                                                        new_blocks_received_from_bdn,
                                                                        new_tx_received_from_blockchain_node,
                                                                        new_tx_received_from_bdn),
                                             BdnPerformanceStatsMessage)

        self.assertEqual(start_time, bdn_stats_msg.interval_start_time())
        self.assertEqual(end_time, bdn_stats_msg.interval_end_time())
        self.assertEqual(new_blocks_received_from_blockchain_node, bdn_stats_msg.new_blocks_from_blockchain_node())
        self.assertEqual(new_blocks_received_from_bdn, bdn_stats_msg.new_blocks_from_bdn())
        self.assertEqual(new_tx_received_from_blockchain_node, bdn_stats_msg.new_tx_from_blockchain_node())
        self.assertEqual(new_tx_received_from_bdn, bdn_stats_msg.new_tx_from_bdn())
