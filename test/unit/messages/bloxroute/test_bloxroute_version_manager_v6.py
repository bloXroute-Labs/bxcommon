from bxcommon import constants
from bxcommon.constants import EMPTY_SOURCE_ID, QUOTA_FLAG_LEN
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.messages.bloxroute.abstract_broadcast_message import AbstractBroadcastMessage
from bxcommon.messages.bloxroute.bloxroute_version_manager import bloxroute_version_manager
from bxcommon.messages.bloxroute.tx_message import TxMessage
from bxcommon.messages.bloxroute.tx_service_sync_txs_message import TxServiceSyncTxsMessage, TxContentShortIds
from bxcommon.messages.bloxroute.v6.tx_message_converter_v6 import tx_message_converter_v6
from bxcommon.messages.bloxroute.v6.tx_message_v6 import TxMessageV6
from bxcommon.messages.bloxroute.v6.tx_service_sync_txs_message_v6 import TxServiceSyncTxsMessageV6, TxContentShortIdsV6
from bxcommon.test_utils import helpers
from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.utils import crypto, uuid_pack
from bxcommon.utils.object_hash import Sha256Hash
from bxcommon.models.tx_quota_type_model import TxQuotaType

NEW_VERSION_SOURCE_ID = uuid_pack.from_bytes(b"\x01" * 16)
EMPTY_SOURCE_ID_STR = EMPTY_SOURCE_ID.decode()


class BloxrouteTxVersionManagerV6Test(AbstractTestCase):

    def test_tx_message(self):
        tx_hash = Sha256Hash(helpers.generate_bytes(crypto.SHA256_HASH_LEN))
        tx_contents = helpers.generate_bytes(250)
        network_num = 1234
        self._test_to_old_version(TxMessage(message_hash=tx_hash, network_num=network_num,
                                            tx_val=tx_contents, quota_type=TxQuotaType.PAID_DAILY_QUOTA))
        self._test_to_new_version(TxMessageV6(message_hash=tx_hash, network_num=network_num, tx_val=tx_contents))

    def _test_to_old_version(self, new_version_msg: TxMessage):
        old_version_msg = bloxroute_version_manager.convert_message_to_older_version(6, new_version_msg)
        self._validate_messages_match(old_version_msg, new_version_msg)

    def _test_to_new_version(self, old_version_msg: TxMessageV6):
        new_version_msg: AbstractBroadcastMessage = \
            bloxroute_version_manager.convert_message_from_older_version(6, old_version_msg)
        self._validate_messages_match(old_version_msg, new_version_msg)
        self.assertEqual(EMPTY_SOURCE_ID_STR, new_version_msg.source_id())

    def _validate_messages_match(self, old_version_msg, new_version_msg):
        self.assertEqual(old_version_msg.msg_type(), new_version_msg.msg_type())
        self.assertEqual(old_version_msg.payload_len(), new_version_msg.payload_len() - QUOTA_FLAG_LEN)
        self.assertEqual(old_version_msg.rawbytes()[
                         AbstractBloxrouteMessage.HEADER_LENGTH:tx_message_converter_v6._LEFT_BREAKPOINT],
                         new_version_msg.rawbytes()[
                         AbstractBloxrouteMessage.HEADER_LENGTH:tx_message_converter_v6._LEFT_BREAKPOINT])
        self.assertEqual(old_version_msg.rawbytes()[tx_message_converter_v6._LEFT_BREAKPOINT:],
                         new_version_msg.rawbytes()[tx_message_converter_v6._RIGHT_BREAKPOINT:])


class BloxrouteTxSyncVersionManagerV6Test(AbstractTestCase):

    def test_tx_sync_message(self):
        _get_next_fake_sid = (i for i in range(1, 100000))
        tx_content_short_ids_v6 = []
        tx_content_short_ids = []
        for i in range(100):
            tx_hash = Sha256Hash(helpers.generate_bytes(crypto.SHA256_HASH_LEN))
            tx_contents = helpers.generate_bytes(250)
            short_ids = [_get_next_fake_sid.__next__() for i in range(0, 1 + i % 7)]
            tx_content_short_ids.append(TxContentShortIds(tx_hash, tx_contents, short_ids,
                                                          [TxQuotaType.NONE for _ in short_ids]))
            tx_content_short_ids_v6.append(TxContentShortIdsV6(tx_hash, tx_contents, short_ids))
        network_num = 1234
        new_version_msg = TxServiceSyncTxsMessage(network_num, tx_content_short_ids)
        old_version_msg = TxServiceSyncTxsMessageV6(network_num, tx_content_short_ids_v6)

        converted_to_old_version = bloxroute_version_manager.convert_message_to_older_version(6, new_version_msg)
        converted_to_new_version = bloxroute_version_manager.convert_message_from_older_version(6, old_version_msg)

        self.validate_message(converted_to_old_version, new_version_msg)
        self.validate_message(old_version_msg, converted_to_new_version)

    def validate_message(self, old_version_msg, new_version_msg):
        self.assertEqual(old_version_msg.msg_type(), new_version_msg.msg_type())
        self.assertEqual(old_version_msg.network_num(), new_version_msg.network_num())
        self.assertEqual(old_version_msg.tx_count(), new_version_msg.tx_count())

        for old_item, new_item in zip(old_version_msg.txs_content_short_ids(), new_version_msg.txs_content_short_ids()):
            self.assertEqual(old_item.tx_hash, new_item.tx_hash)
            self.assertEqual(old_item.tx_content, new_item.tx_content)
            self.assertEqual(old_item.short_ids, new_item.short_ids)
