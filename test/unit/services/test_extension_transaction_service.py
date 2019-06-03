from bxcommon.services.extension_transaction_service import ExtensionTransactionService
from bxcommon.services.transaction_service import TransactionService
from bxcommon.test_utils.abstract_transaction_service_test_case import AbstractTransactionServiceTestCase


class ExtensionTransactionServiceTest(AbstractTransactionServiceTestCase):
    def get_transaction_service(self) -> TransactionService:
        return ExtensionTransactionService(self.mock_node, 0)
