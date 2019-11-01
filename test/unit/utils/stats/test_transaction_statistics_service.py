import struct
from typing import Optional

from mock import MagicMock

from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.test_utils.mocks.mock_node import MockNode
from bxcommon.test_utils import helpers
from bxcommon.utils import crypto
from bxcommon.utils.object_hash import Sha256Hash
from bxcommon.utils.stats.transaction_stat_event_type import TransactionStatEventType
from bxcommon.utils.stats.transaction_statistics_service import tx_stats


class TransactionStatisticsServiceTest(AbstractTestCase):

    def setUp(self):
        self.node = MockNode(helpers.get_common_opts(8888))
        tx_stats.set_node(self.node)
        tx_stats.configure_network(1, 0.5)
        tx_stats.configure_network(2, 50)

    def test_should_log_event_tx_hash(self):

        # testing that only 0.5% of transactions based on last byte are being logged
        self._test_should_log_event(255, 1, None, False)
        self._test_should_log_event(100, 1, None, False)
        self._test_should_log_event(16, 1, None, False)
        self._test_should_log_event(1, 1, None, True)
        self._test_should_log_event(0, 1, None, True)

    def test_should_log_event_short_id(self):
        self._test_should_log_event(255, 1, 100, False)
        self._test_should_log_event(255, 1, 999, False)
        self._test_should_log_event(255, 1, 10, False)
        self._test_should_log_event(255, 1, 5, True)
        self._test_should_log_event(255, 1, 1, True)

    def test_should_log_event_network_num(self):
        self._test_should_log_event(255, 1, None, False)
        self._test_should_log_event(255, 2, None, False)
        self._test_should_log_event(100, 1, None, False)
        self._test_should_log_event(100, 2, None, True)

    def _test_should_log_event(self, last_byte_value: int, network_num: int, short_id: Optional[int],
                               expected_to_log: bool):

        tx_stats.logger.log = MagicMock()

        tx_hash = helpers.generate_bytearray(crypto.SHA256_HASH_LEN)
        struct.pack_into("<B", tx_hash, crypto.SHA256_HASH_LEN - 1, last_byte_value)
        tx_stats.add_tx_by_hash_event(Sha256Hash(tx_hash), TransactionStatEventType.TX_SENT_FROM_GATEWAY_TO_PEERS,
                                      network_num, short_id)
        if expected_to_log:
            tx_stats.logger.log.assert_called_once()
        else:
            tx_stats.logger.log.assert_not_called()
