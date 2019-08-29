import time
from abc import abstractmethod, ABCMeta

from bxcommon import constants
from bxcommon.connections.node_type import NodeType
from bxcommon.utils.stats.memory_statistics_service import memory_statistics
from mock import MagicMock

from bxcommon.constants import NULL_TX_SID
from bxcommon.services.transaction_service import TransactionService
from bxcommon.test_utils import helpers
from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.test_utils.mocks.mock_node import MockNode
from bxcommon.utils import crypto
from bxcommon.utils.object_hash import Sha256Hash


def get_sha(data: bytes) -> Sha256Hash:
    return Sha256Hash(binary=crypto.double_sha256(data))


class AbstractTransactionServiceTestCase(AbstractTestCase):
    __metaclass__ = ABCMeta

    TEST_MEMORY_LIMIT_MB = 0.01

    def setUp(self) -> None:
        self.mock_node = MockNode(helpers.get_common_opts(8000, node_type=NodeType.GATEWAY))
        self.mock_node.opts.transaction_pool_memory_limit = self.TEST_MEMORY_LIMIT_MB
        self.transaction_service = self._get_transaction_service()

    def _test_sid_assignment_basic(self):
        short_ids = [1, 2, 3, 4, 5]
        transaction_hashes = list(map(crypto.double_sha256, map(bytes, short_ids)))
        transaction_contents = list(map(crypto.double_sha256, transaction_hashes))

        for i in range(len(short_ids)):
            self.transaction_service.assign_short_id(transaction_hashes[i], short_ids[i])
            self.transaction_service.set_transaction_contents(transaction_hashes[i], transaction_contents[i])

        for i, transaction_hash in enumerate(transaction_hashes):
            self.assertEqual(short_ids[i], self.transaction_service.get_short_id(transaction_hash))

        for i, short_id in enumerate(short_ids):
            transaction_hash, transaction_content, assigned_short_id = self.transaction_service.get_transaction(short_id)
            self.assertEqual(transaction_hashes[i], transaction_hash.binary)
            self.assertEqual(transaction_contents[i], transaction_content)
            self.assertEqual(short_id, assigned_short_id)

        self.assertTrue(self.transaction_service.tx_assign_alarm_scheduled)
        self.assertEqual(len(short_ids), len(self.transaction_service._tx_assignment_expire_queue))

    def _test_sid_assignment_multiple_sids(self):
        short_ids = [1, 2, 3, 4, 5]
        short_ids_2 = [6, 7, 8, 9, 10]
        transaction_hashes = list(map(crypto.double_sha256, map(bytes, short_ids)))
        transaction_contents = list(map(crypto.double_sha256, transaction_hashes))

        for i in range(len(short_ids)):
            self.transaction_service.assign_short_id(transaction_hashes[i], short_ids[i])
            self.transaction_service.assign_short_id(transaction_hashes[i], short_ids_2[i])
            self.transaction_service.set_transaction_contents(transaction_hashes[i], transaction_contents[i])

        for i, transaction_hash in enumerate(transaction_hashes):
            short_id = self.transaction_service.get_short_id(transaction_hash)
            self.assertTrue(short_id == short_ids[i] or short_id == short_ids_2[i])

        for i in range(len(short_ids)):
            transaction_hash1, transaction_content1, _ = self.transaction_service.get_transaction(short_ids[i])
            transaction_hash2, transaction_content2, _ = self.transaction_service.get_transaction(short_ids_2[i])
            self.assertEqual(transaction_hashes[i], transaction_hash1.binary)
            self.assertEqual(transaction_contents[i], transaction_content1)
            self.assertEqual(transaction_hashes[i], transaction_hash2.binary)
            self.assertEqual(transaction_contents[i], transaction_content2)

    def _test_sid_expiration(self):
        short_ids = [1, 2, 3, 4, 5]
        transaction_hashes = list(map(crypto.double_sha256, map(bytes, short_ids)))
        transaction_contents = list(map(crypto.double_sha256, transaction_hashes))

        for i in range(len(short_ids)):
            self.transaction_service.assign_short_id(transaction_hashes[i], short_ids[i])
            cache_key = self.transaction_service._tx_hash_to_cache_key(transaction_hashes[i])
            self.transaction_service._tx_cache_key_to_contents[cache_key] = transaction_contents[i]

        time.time = MagicMock(return_value=time.time() + self.transaction_service.node.opts.sid_expire_time + 10)
        self.transaction_service.node.alarm_queue.fire_alarms()

        self.assertFalse(self.transaction_service.tx_assign_alarm_scheduled)
        self.assertEqual(0, len(self.transaction_service._tx_assignment_expire_queue))

        for short_id in short_ids:
            transaction_hash, transaction_content, _ = self.transaction_service.get_transaction(short_id)
            self.assertIsNone(transaction_hash)
            self.assertIsNone(transaction_content)

        for transaction_hash in transaction_hashes:
            self.assertEqual(NULL_TX_SID, self.transaction_service.get_short_id(transaction_hash))

    def _test_expire_old_assignments(self):
        tx_expire_time = self.transaction_service.node.opts.sid_expire_time

        first_tx_time = time.time()
        time.time = MagicMock(return_value=first_tx_time)
        tx_hash_1 = Sha256Hash(helpers.generate_bytearray(crypto.SHA256_HASH_LEN))
        tx_contents_1 = helpers.generate_bytearray(500)
        self.transaction_service.set_transaction_contents(tx_hash_1, tx_contents_1)
        self.transaction_service.assign_short_id(tx_hash_1, 1)

        second_tx_time = first_tx_time + 1000
        time.time = MagicMock(return_value=second_tx_time)
        tx_hash_2 = Sha256Hash(helpers.generate_bytearray(crypto.SHA256_HASH_LEN))
        tx_contents_2 = helpers.generate_bytearray(500)
        self.transaction_service.set_transaction_contents(tx_hash_2, tx_contents_2)
        self.transaction_service.assign_short_id(tx_hash_2, 2)

        third_tx_time = second_tx_time + 3
        time.time = MagicMock(return_value=third_tx_time)
        tx_hash_3 = Sha256Hash(helpers.generate_bytearray(crypto.SHA256_HASH_LEN))
        tx_contents_3 = helpers.generate_bytearray(500)
        self.transaction_service.set_transaction_contents(tx_hash_3, tx_contents_3)
        self.transaction_service.assign_short_id(tx_hash_3, 3)

        expire_run_time = first_tx_time + tx_expire_time + 1
        time.time = MagicMock(return_value=expire_run_time)
        expire_repeat_time = self.transaction_service.expire_old_assignments()
        self.assertEqual(999, int(expire_repeat_time))

        expire_run_time = second_tx_time + tx_expire_time + 1
        time.time = MagicMock(return_value=expire_run_time)
        expire_repeat_time = self.transaction_service.expire_old_assignments()
        self.assertEqual(constants.MIN_CLEAN_UP_EXPIRED_TXS_TASK_INTERVAL_S, expire_repeat_time)

        expire_run_time = third_tx_time + tx_expire_time + 1
        time.time = MagicMock(return_value=expire_run_time)
        expire_repeat_time = self.transaction_service.expire_old_assignments()
        self.assertEqual(0, expire_repeat_time)

    def _test_sid_expiration_multiple_sids(self):
        short_ids = [0, 1, 2, 3, 4]
        transaction_hashes = list(map(crypto.double_sha256, map(bytes, short_ids)))
        transaction_contents = list(map(crypto.double_sha256, transaction_hashes))

        for i in range(len(short_ids)):
            self.transaction_service.assign_short_id(transaction_hashes[i], short_ids[i])
            self.transaction_service.set_transaction_contents(transaction_hashes[i], transaction_contents[i])

        time_zero = time.time()

        time.time = MagicMock(return_value=time_zero + self.transaction_service.node.opts.sid_expire_time / 2)
        short_ids_2 = [5, 6, 7, 8, 9]
        for i in range(len(short_ids_2)):
            self.transaction_service.assign_short_id(transaction_hashes[i], short_ids_2[i])

        time.time = MagicMock(return_value=time_zero + self.transaction_service.node.opts.sid_expire_time + 5)
        self.transaction_service.node.alarm_queue.fire_alarms()

        self.assertTrue(self.transaction_service.tx_assign_alarm_scheduled)
        self.assertEqual(len(short_ids_2), len(self.transaction_service._tx_assignment_expire_queue))

        for short_id in short_ids:
            transaction_hash, transaction_content, _ = self.transaction_service.get_transaction(short_id)
            self.assertIsNone(transaction_hash)
            self.assertIsNone(transaction_content)

        for i, short_id in enumerate(short_ids_2):
            transaction_hash, transaction_content, _ = self.transaction_service.get_transaction(short_id)
            self.assertEqual(transaction_hashes[i], transaction_hash.binary)
            self.assertEqual(transaction_contents[i], transaction_content)

        for i, transaction_hash in enumerate(transaction_hashes):
            self.assertEqual(short_ids_2[i], self.transaction_service.get_short_id(transaction_hash))

    def _test_track_short_ids_seen_in_block(self):
        short_ids = [1, 2, 3, 4, 5]
        transaction_hashes = list(map(crypto.double_sha256, map(bytes, short_ids)))
        transaction_contents = list(map(crypto.double_sha256, transaction_hashes))

        for i in range(len(short_ids)):
            self.transaction_service.assign_short_id(transaction_hashes[i], short_ids[i])
            cached_key = self.transaction_service._tx_hash_to_cache_key(transaction_hashes[i])
            self.transaction_service._tx_cache_key_to_contents[cached_key] = transaction_contents[i]

        self.transaction_service.set_final_tx_confirmations_count(7)
        # 1st block with short ids arrives
        block_hash = bytearray(helpers.generate_bytearray(32))
        self.transaction_service.track_seen_short_ids(Sha256Hash(block_hash), [1])
        self._verify_txs_in_tx_service([1, 2, 3, 4, 5], [])

        # 2nd block with short ids arrives
        block_hash = bytearray(helpers.generate_bytearray(32))
        self.transaction_service.track_seen_short_ids(Sha256Hash(block_hash), [2])
        self._verify_txs_in_tx_service([1, 2, 3, 4, 5], [])

        # 3rd block with short ids arrives
        block_hash = bytearray(helpers.generate_bytearray(32))
        self.transaction_service.track_seen_short_ids(Sha256Hash(block_hash), [3, 4])
        self._verify_txs_in_tx_service([1, 2, 3, 4, 5], [])

        # 4th block with short ids arrives
        block_hash = bytearray(helpers.generate_bytearray(32))
        self.transaction_service.track_seen_short_ids(Sha256Hash(block_hash), [])
        self._verify_txs_in_tx_service([1, 2, 3, 4, 5], [])


        # 5th block with short ids arrives
        block_hash = bytearray(helpers.generate_bytearray(32))
        self.transaction_service.track_seen_short_ids(Sha256Hash(block_hash), [])
        self._verify_txs_in_tx_service([1, 2, 3, 4, 5], [])

        # 6th block with short ids arrives
        block_hash = bytearray(helpers.generate_bytearray(32))
        self.transaction_service.track_seen_short_ids(Sha256Hash(block_hash), [])
        self._verify_txs_in_tx_service([1, 2, 3, 4, 5], [])

        # 7th block with short ids arrives
        block_hash = bytearray(helpers.generate_bytearray(32))
        self.transaction_service.track_seen_short_ids(Sha256Hash(block_hash), [])
        self._verify_txs_in_tx_service([2, 3, 4], [0, 1])

        # 8th block with short ids arrives
        block_hash = bytearray(helpers.generate_bytearray(32))
        self.transaction_service.track_seen_short_ids(Sha256Hash(block_hash), [])
        self._verify_txs_in_tx_service([3, 4], [0, 1, 2])

        # 9th block with short ids arrives
        block_hash = bytearray(helpers.generate_bytearray(32))
        self.transaction_service.track_seen_short_ids(Sha256Hash(block_hash), [])
        self._verify_txs_in_tx_service([], [0, 1, 2, 3, 4])

    def _test_track_short_ids_seen_in_block_multiple_per_tx(self):
        short_ids = [1, 2, 3, 4, 5]
        transaction_hashes = list(map(crypto.double_sha256, map(bytes, short_ids)))
        transaction_contents = list(map(crypto.double_sha256, transaction_hashes))

        for i in range(len(short_ids)):
            self.transaction_service.assign_short_id(transaction_hashes[i], short_ids[i])
            cached_key = self.transaction_service._tx_hash_to_cache_key(transaction_hashes[i])
            self.transaction_service._tx_cache_key_to_contents[cached_key] = transaction_contents[i]

        self.transaction_service.set_final_tx_confirmations_count(2)

        # assign multiple shorts ids to one of the transactions
        first_cached_key = self.transaction_service._tx_hash_to_cache_key(transaction_hashes[0])
        self.transaction_service.assign_short_id(first_cached_key, 10)
        self.transaction_service.assign_short_id(first_cached_key, 11)

        # 1st block with short ids arrives
        block_hash = bytearray(helpers.generate_bytearray(32))
        self.transaction_service.track_seen_short_ids(Sha256Hash(block_hash), [1, 2])
        self._verify_txs_in_tx_service([1, 2, 3, 4, 5, 10, 11], [])
        self.assertTrue(self.transaction_service.has_transaction_contents(transaction_hashes[0]))
        self.assertTrue(self.transaction_service.has_transaction_contents(transaction_hashes[1]))

        # 2nd block with short ids arrives
        block_hash = bytearray(helpers.generate_bytearray(32))
        self.transaction_service.track_seen_short_ids(Sha256Hash(block_hash), [3])
        self._verify_txs_in_tx_service([3, 4, 5], [1, 2, 10, 11])
        self.assertFalse(self.transaction_service.has_transaction_contents(transaction_hashes[0]))
        self.assertFalse(self.transaction_service.has_transaction_contents(transaction_hashes[1]))
        self.assertTrue(self.transaction_service.has_transaction_contents(transaction_hashes[2]))


        # 3rd block with short ids arrives
        block_hash = bytearray(helpers.generate_bytearray(32))
        self.transaction_service.track_seen_short_ids(Sha256Hash(block_hash), [4, 5])
        self._verify_txs_in_tx_service([4, 5], [1, 2, 3, 10, 11])
        self.assertFalse(self.transaction_service.has_transaction_contents(transaction_hashes[2]))
        self.assertTrue(self.transaction_service.has_transaction_contents(transaction_hashes[3]))
        self.assertTrue(self.transaction_service.has_transaction_contents(transaction_hashes[4]))

        # 4th block with short ids arrives
        block_hash = bytearray(helpers.generate_bytearray(32))
        self.transaction_service.track_seen_short_ids(Sha256Hash(block_hash), [])
        self._verify_txs_in_tx_service([], [1, 2, 3, 4, 5, 10, 11])
        self.assertFalse(self.transaction_service.has_transaction_contents(transaction_hashes[3]))
        self.assertFalse(self.transaction_service.has_transaction_contents(transaction_hashes[4]))

    def _test_transactions_contents_memory_limit(self):
        tx_size = 500
        memory_limit_bytes = int(self.TEST_MEMORY_LIMIT_MB * 1000000)
        tx_count_set_1 = memory_limit_bytes / tx_size

        transactions_set_1 = self._add_transactions(tx_count_set_1, tx_size)

        self.assertEqual(memory_limit_bytes, self.transaction_service._total_tx_contents_size)
        stats = self.transaction_service.get_tx_service_aggregate_stats()
        self.assertEqual(0, stats["transactions_removed_by_memory_limit"])
        self.assertEqual(tx_count_set_1, len(self.transaction_service._tx_cache_key_to_contents))

        # adding transactions that does not fit into memory limit
        tx_count_set_2 = tx_count_set_1 / 2
        transactions_set_2 = self._add_transactions(tx_count_set_2, tx_size, short_id_offset=100)
        self.assertEqual(memory_limit_bytes, self.transaction_service._total_tx_contents_size)
        stats = self.transaction_service.get_tx_service_aggregate_stats()
        self.assertEqual(tx_count_set_2, stats["transactions_removed_by_memory_limit"])
        self.assertEqual(tx_count_set_1, len(self.transaction_service._tx_cache_key_to_contents))

        # verify that first half of transactions from set 1 no longer in cache and second half still cached
        for i in range(len(transactions_set_1)):
            tx_hash, tx_contents, short_id = transactions_set_1[i]
            if i < tx_count_set_2:
                self.assertFalse(self.transaction_service.has_transaction_contents(tx_hash))
                self.assertFalse(self.transaction_service.has_transaction_short_id(tx_hash))
                self.assertFalse(self.transaction_service.has_short_id(short_id))
            else:
                self.assertTrue(self.transaction_service.has_transaction_contents(tx_hash))
                self.assertTrue(self.transaction_service.has_transaction_short_id(tx_hash))
                self.assertTrue(self.transaction_service.has_short_id(short_id))
                self.assertEqual((tx_hash, tx_contents, short_id), self.transaction_service.get_transaction(short_id))
                self.assertEqual(tx_contents, self.transaction_service.get_transaction_by_hash(tx_hash))

        # verify that all transactions from the second set are in cache
        for i in range(len(transactions_set_2)):
            tx_hash, tx_contents, short_id = transactions_set_2[i]
            self.assertTrue(self.transaction_service.has_transaction_contents(tx_hash))
            self.assertTrue(self.transaction_service.has_transaction_short_id(tx_hash))
            self.assertTrue(self.transaction_service.has_short_id(short_id))
            self.assertEqual((tx_hash, tx_contents, short_id), self.transaction_service.get_transaction(short_id))
            self.assertEqual(tx_contents, self.transaction_service.get_transaction_by_hash(tx_hash))

        # add transaction that is twice longer
        self._add_transactions(1, tx_size * 2)
        stats = self.transaction_service.get_tx_service_aggregate_stats()
        self.assertEqual(tx_count_set_2 + 2, stats["transactions_removed_by_memory_limit"])
        self.assertEqual(tx_count_set_1 - 1, len(self.transaction_service._tx_cache_key_to_contents))

    def _test_get_missing_transactions(self):
        existing_short_ids = list(range(1, 51))
        missing_short_ids = list(range(51, 101))
        missing_transaction_hashes = list(map(get_sha, map(bytes, missing_short_ids[:25])))
        existing_transaction_hashes = list(map(get_sha, map(bytes, missing_short_ids[25:])))
        transaction_hashes = existing_transaction_hashes + missing_transaction_hashes

        transaction_contents = [crypto.double_sha256(sha.binary) for sha in missing_transaction_hashes]
        for idx, existing_short_id in enumerate(existing_short_ids):
            self.transaction_service.assign_short_id(transaction_hashes[idx], existing_short_id)
        for idx, transaction_hash in enumerate(existing_transaction_hashes):
            self.transaction_service.set_transaction_contents(transaction_hash, transaction_contents[idx])
        has_missing, unknown_short_ids, unknown_hashes = \
            self.transaction_service.get_missing_transactions(
                existing_short_ids + missing_short_ids
            )
        self.assertTrue(has_missing)
        self.assertEqual(missing_short_ids, unknown_short_ids)
        self.assertEqual(missing_transaction_hashes, unknown_hashes)

    def _test_verify_tx_removal_by_hash(self):
        short_ids = [1, 2, 3, 4]
        transaction_hashes = list(map(crypto.double_sha256, map(bytes, short_ids)))
        transaction_contents = list(map(crypto.double_sha256, transaction_hashes))

        for i in range(len(short_ids)):
            self.transaction_service.set_transaction_contents(transaction_hashes[i], transaction_contents[i])
            self.transaction_service.assign_short_id(transaction_hashes[i], short_ids[i])

        self._verify_txs_in_tx_service(expected_short_ids=[1, 2, 3, 4], not_expected_short_ids=[])

        for tx_hash in transaction_hashes:
            self.transaction_service.remove_transaction_by_tx_hash(tx_hash)
        self._verify_txs_in_tx_service(expected_short_ids=[], not_expected_short_ids=[0, 1, 2, 3, 4])

    def _test_memory_stats(self):
        self._add_transactions(1000, 100)
        self.transaction_service.log_tx_service_mem_stats()
        memory_statistics.flush_info()

    def _add_transactions(self, tx_count, tx_size, short_id_offset=0):
        transactions = []

        for i in range(int(tx_count)):
            tx_hash = Sha256Hash(binary=helpers.generate_bytearray(crypto.SHA256_HASH_LEN))
            tx_content = helpers.generate_bytearray(tx_size)
            short_id = short_id_offset + i + 1

            self.transaction_service.set_transaction_contents(tx_hash, tx_content)
            self.transaction_service.assign_short_id(tx_hash, short_id)

            transactions.append((tx_hash, tx_content, short_id))

        return transactions

    def _verify_txs_in_tx_service(self, expected_short_ids, not_expected_short_ids):
        for short_id in expected_short_ids:
            self.assertIsNotNone(self.transaction_service.get_transaction(short_id).hash)

        for short_id in not_expected_short_ids:
            self.assertIsNone(self.transaction_service.get_transaction(short_id).hash)
            self.assertIsNone(self.transaction_service.get_transaction(short_id).contents)
            self.assertNotIn(short_id, self.transaction_service._tx_assignment_expire_queue.queue)

    @abstractmethod
    def _get_transaction_service(self) -> TransactionService:
        pass
