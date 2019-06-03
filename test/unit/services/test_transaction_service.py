from bxcommon.services.transaction_service import TransactionService
from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.test_utils.abstract_transaction_service_test_case import AbstractTransactionServiceTestCase


class TransactionServiceTest(AbstractTransactionServiceTestCase):
    def get_transaction_service(self) -> TransactionService:
        return TransactionService(self.mock_node, 0)
