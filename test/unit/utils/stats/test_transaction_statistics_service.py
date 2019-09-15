import struct

from mock import MagicMock

from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.test_utils.mocks.mock_node import MockNode
from bxcommon.test_utils import helpers
from bxcommon.utils import crypto
from bxcommon.utils.stats.transaction_stat_event_type import TransactionStatEventType
from bxcommon.utils.stats.transaction_statistics_service import tx_stats


class TransactionStatisticsServiceTest(AbstractTestCase):

    def setUp(self):
        self.node = MockNode(helpers.get_common_opts(8888))
        tx_stats.set_node(self.node)

    def test_should_log_event(self):

        # testing that only 5% of transactions based on last byte are being logged
        self._test_should_log_event(255, False)
        self._test_should_log_event(100, False)
        self._test_should_log_event(16, False)
        self._test_should_log_event(1, True)
        self._test_should_log_event(0, True)

        # self._test_should_log_event(15, True)

    def _test_should_log_event(self, last_byte_value, expected_to_log):

        tx_stats.logger.log = MagicMock()

        tx_hash = helpers.generate_bytearray(crypto.SHA256_HASH_LEN)
        struct.pack_into("<B", tx_hash, crypto.SHA256_HASH_LEN - 1, last_byte_value)
        tx_stats.add_tx_by_hash_event(tx_hash, TransactionStatEventType.TX_SENT_FROM_GATEWAY_TO_PEERS)
        if expected_to_log:
            tx_stats.logger.log.assert_called_once()
        else:
            tx_stats.logger.log.assert_not_called()
