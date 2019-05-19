from bxcommon.services.extension_transaction_service import ExtensionTransactionService
from bxcommon.services.transaction_service import TransactionService
from bxcommon.test_utils.abstract_transaction_service_test_case import AbstractTransactionServiceTestCase


class ExtensionTransactionServiceTest(AbstractTransactionServiceTestCase):

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

    def _get_transaction_service(self) -> TransactionService:
        return ExtensionTransactionService(self.mock_node, 0)
