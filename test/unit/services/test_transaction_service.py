from bxcommon.services.transaction_service import TransactionService
from bxcommon.test_utils.abstract_transaction_service_test_case import AbstractTransactionServiceTestCase


class TransactionServiceTest(AbstractTransactionServiceTestCase):

    def test_get_missing_transactions(self):
        self._test_get_missing_transactions()

    def test_sid_assignment_basic(self):
        self._test_sid_assignment_basic()

    def test_sid_assignment_multiple_sids(self):
        self._test_sid_assignment_multiple_sids()

    def test_sid_expiration(self):
        self._test_sid_expiration()

    def test_sid_expiration_multiple_sids(self):
        self._test_sid_expiration_multiple_sids()

    def test_track_short_ids_seen_in_block(self):
        self._test_track_short_ids_seen_in_block()

    def test_transactions_contents_memory_limit(self):
        self._test_transactions_contents_memory_limit()

    def test_track_short_ids_seen_in_block_mutiple_per_tx(self):
        self._test_track_short_ids_seen_in_block_mutiple_per_tx()

    def _get_transaction_service(self) -> TransactionService:
        return TransactionService(self.mock_node, 0)
