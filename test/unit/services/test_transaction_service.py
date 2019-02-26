import time

from mock import MagicMock

from bxcommon.constants import LOCALHOST, NULL_TX_SID
from bxcommon.services.transaction_service import TransactionService
from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.test_utils.mocks.mock_node import MockNode
from bxcommon.utils import crypto


class TransactionServiceTest(AbstractTestCase):

    def setUp(self):
        self.transaction_service = TransactionService(MockNode(LOCALHOST, 8000), 0)

    def test_sid_assignment_basic(self):
        short_ids = [1, 2, 3, 4, 5]
        transaction_hashes = map(crypto.double_sha256, map(str, short_ids))
        transaction_contents = map(crypto.double_sha256, transaction_hashes)

        for i in xrange(len(short_ids)):
            self.transaction_service.assign_short_id(transaction_hashes[i], short_ids[i])
            self.transaction_service.txhash_to_contents[transaction_hashes[i]] = transaction_contents[i]

        for i, transaction_hash in enumerate(transaction_hashes):
            self.assertEqual(short_ids[i], self.transaction_service.get_short_id(transaction_hash))

        for i, short_id in enumerate(short_ids):
            transaction_hash, transaction_content = self.transaction_service.get_transaction(short_id)
            self.assertEqual(transaction_hashes[i], transaction_hash)
            self.assertEqual(transaction_contents[i], transaction_content)

        self.assertTrue(self.transaction_service.tx_assign_alarm_scheduled)
        self.assertEquals(len(short_ids), len(self.transaction_service.tx_assignment_expire_queue))

    def test_sid_assignment_multiple_sids(self):
        short_ids = [1, 2, 3, 4, 5]
        short_ids_2 = [6, 7, 8, 9, 10]
        transaction_hashes = map(crypto.double_sha256, map(str, short_ids))
        transaction_contents = map(crypto.double_sha256, transaction_hashes)

        for i in xrange(len(short_ids)):
            self.transaction_service.assign_short_id(transaction_hashes[i], short_ids[i])
            self.transaction_service.assign_short_id(transaction_hashes[i], short_ids_2[i])
            self.transaction_service.txhash_to_contents[transaction_hashes[i]] = transaction_contents[i]

        for i, transaction_hash in enumerate(transaction_hashes):
            short_id = self.transaction_service.get_short_id(transaction_hash)
            self.assertTrue(short_id == short_ids[i] or short_id == short_ids_2[i])

        for i in xrange(len(short_ids)):
            transaction_hash1, transaction_content1 = self.transaction_service.get_transaction(short_ids[i])
            transaction_hash2, transaction_content2 = self.transaction_service.get_transaction(short_ids_2[i])
            self.assertEqual(transaction_hashes[i], transaction_hash1)
            self.assertEqual(transaction_contents[i], transaction_content1)
            self.assertEqual(transaction_hashes[i], transaction_hash2)
            self.assertEqual(transaction_contents[i], transaction_content2)

    def test_sid_expiration(self):
        short_ids = [1, 2, 3, 4, 5]
        transaction_hashes = map(crypto.double_sha256, map(str, short_ids))
        transaction_contents = map(crypto.double_sha256, transaction_hashes)

        for i in xrange(len(short_ids)):
            self.transaction_service.assign_short_id(transaction_hashes[i], short_ids[i])
            self.transaction_service.txhash_to_contents[transaction_hashes[i]] = transaction_contents[i]

        time.time = MagicMock(return_value=time.time() + self.transaction_service.node.opts.sid_expire_time + 10)
        self.transaction_service.node.alarm_queue.fire_alarms()

        self.assertFalse(self.transaction_service.tx_assign_alarm_scheduled)
        self.assertEqual(0, len(self.transaction_service.tx_assignment_expire_queue))

        for short_id in short_ids:
            transaction_hash, transaction_content = self.transaction_service.get_transaction(short_id)
            self.assertIsNone(transaction_hash)
            self.assertIsNone(transaction_content)

        for transaction_hash in transaction_hashes:
            self.assertEqual(NULL_TX_SID, self.transaction_service.get_short_id(transaction_hash))

    def test_sid_expiration_multiple_sids(self):
        short_ids = [0, 1, 2, 3, 4]
        transaction_hashes = map(crypto.double_sha256, map(str, short_ids))
        transaction_contents = map(crypto.double_sha256, transaction_hashes)

        for i in xrange(len(short_ids)):
            self.transaction_service.assign_short_id(transaction_hashes[i], short_ids[i])
            self.transaction_service.txhash_to_contents[transaction_hashes[i]] = transaction_contents[i]

        time_zero = time.time()

        time.time = MagicMock(return_value=time_zero + self.transaction_service.node.opts.sid_expire_time / 2)
        short_ids_2 = [5, 6, 7, 8, 9]
        for i in xrange(len(short_ids_2)):
            self.transaction_service.assign_short_id(transaction_hashes[i], short_ids_2[i])

        time.time = MagicMock(return_value=time_zero + self.transaction_service.node.opts.sid_expire_time + 5)
        self.transaction_service.node.alarm_queue.fire_alarms()

        self.assertTrue(self.transaction_service.tx_assign_alarm_scheduled)
        self.assertEqual(len(short_ids_2), len(self.transaction_service.tx_assignment_expire_queue))

        for short_id in short_ids:
            transaction_hash, transaction_content = self.transaction_service.get_transaction(short_id)
            self.assertIsNone(transaction_hash)
            self.assertIsNone(transaction_content)

        for i, short_id in enumerate(short_ids_2):
            transaction_hash, transaction_content = self.transaction_service.get_transaction(short_id)
            self.assertEqual(transaction_hashes[i], transaction_hash)
            self.assertEqual(transaction_contents[i], transaction_content)

        for i, transaction_hash in enumerate(transaction_hashes):
            self.assertEqual(short_ids_2[i], self.transaction_service.get_short_id(transaction_hash))

    def test_track_short_ids_seen_in_block(self):
        short_ids = [0, 1, 2, 3, 4]
        transaction_hashes = map(crypto.double_sha256, map(str, short_ids))
        transaction_contents = map(crypto.double_sha256, transaction_hashes)

        for i in xrange(len(short_ids)):
            self.transaction_service.assign_short_id(transaction_hashes[i], short_ids[i])
            self.transaction_service.txhash_to_contents[transaction_hashes[i]] = transaction_contents[i]

        # 1st block with short ids arrives
        self.transaction_service.track_seen_short_ids([0, 1])
        self._verify_txs_in_tx_service([0, 1, 2, 3, 4], [])

        # 2nd block with short ids arrives
        self.transaction_service.track_seen_short_ids([2])
        self._verify_txs_in_tx_service([0, 1, 2, 3, 4], [])

        # 3rd block with short ids arrives
        self.transaction_service.track_seen_short_ids([3, 4])
        self._verify_txs_in_tx_service([0, 1, 2, 3, 4], [])

        # 4th block with short ids arrives
        self.transaction_service.track_seen_short_ids([])
        self._verify_txs_in_tx_service([0, 1, 2, 3, 4], [])

        # 5th block with short ids arrives
        self.transaction_service.track_seen_short_ids([])
        self._verify_txs_in_tx_service([0, 1, 2, 3, 4], [])

        # 6th block with short ids arrives
        self.transaction_service.track_seen_short_ids([])
        self._verify_txs_in_tx_service([0, 1, 2, 3, 4], [])

        # 7th block with short ids arrives
        self.transaction_service.track_seen_short_ids([])
        self._verify_txs_in_tx_service([2, 3, 4], [0, 1])

        # 8th block with short ids arrives
        self.transaction_service.track_seen_short_ids([])
        self._verify_txs_in_tx_service([3, 4], [0, 1, 2])

        # 9th block with short ids arrives
        self.transaction_service.track_seen_short_ids([])
        self._verify_txs_in_tx_service([], [0, 1, 2, 3, 4])

    def _verify_txs_in_tx_service(self, expected_short_ids, not_expected_short_ids):
        for short_id in expected_short_ids:
            self.assertIsNotNone(self.transaction_service.get_transaction(short_id))

        for short_id in not_expected_short_ids:
            self.assertIsNone(self.transaction_service.get_transaction(short_id)[0])
            self.assertIsNone(self.transaction_service.get_transaction(short_id)[1])

