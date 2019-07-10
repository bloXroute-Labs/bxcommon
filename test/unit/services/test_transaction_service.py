import time

from mock import MagicMock

from bxcommon import constants
from bxcommon.services.transaction_service import TransactionService
from bxcommon.test_utils import helpers
from bxcommon.test_utils.abstract_transaction_service_test_case import AbstractTransactionServiceTestCase
from bxcommon.utils import crypto
from bxcommon.utils.object_hash import Sha256Hash


class TransactionServiceTest(AbstractTransactionServiceTestCase):

    def test_get_missing_transactions(self):
        self._test_get_missing_transactions()

    def test_sid_assignment_basic(self):
        self._test_sid_assignment_basic()

    def test_sid_assignment_multiple_sids(self):
        self._test_sid_assignment_multiple_sids()

    def test_sid_expiration(self):
        self._test_sid_expiration()

    def test_expire_old_assignments(self):
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

    def test_sid_expiration_multiple_sids(self):
        self._test_sid_expiration_multiple_sids()

    def test_track_short_ids_seen_in_block(self):
        self._test_track_short_ids_seen_in_block()

    def test_transactions_contents_memory_limit(self):
        self._test_transactions_contents_memory_limit()

    def test_track_short_ids_seen_in_block_multiple_per_tx(self):
        self._test_track_short_ids_seen_in_block_multiple_per_tx()

    def _get_transaction_service(self) -> TransactionService:
        return TransactionService(self.mock_node, 0)
