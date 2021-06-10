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
        tx_stats.configure_network(1, 0.5, 0.06)
        tx_stats.configure_network(2, 50, 60)
        tx_stats.configure_network(3, 0.001, 60)
        tx_stats.configure_network(4, 0.025, 60)

    def test_should_log_event_tx_hash(self):
        # testing that only 0.5% of transactions based on last byte are being logged
        self._test_should_log_event(0xffff, 1, None, False)
        self._test_should_log_event(0x7d00, 1, None, False)
        self._test_should_log_event(0x3e80, 1, None, False)
        self._test_should_log_event(0x05dc, 1, None, False)
        self._test_should_log_event(0x0012, 1, None, True)

        self._test_should_log_event(0x000a, 3, None, False)
        self._test_should_log_event(0x0000, 3, None, True)

        self._test_should_log_event(0x0000, 4, None, True)
        self._test_should_log_event(0x0010, 4, None, True)
        self._test_should_log_event(0x000f, 4, None, True)
        self._test_should_log_event(0x0011, 4, None, False)

    def test_should_log_event_short_id(self):
        self._test_should_log_event(0xffff, 1, 100, False)
        self._test_should_log_event(0xffff, 1, 999, False)
        self._test_should_log_event(0xffff, 1, 10, False)
        self._test_should_log_event(0xffff, 1, 5, True)
        self._test_should_log_event(0xffff, 1, 1, True)

    def test_should_log_event_network_num(self):
        self._test_should_log_event(0xffff, 1, None, False)
        self._test_should_log_event(0xffff, 2, None, False)
        self._test_should_log_event(0x7530, 1, None, False)
        self._test_should_log_event(0x7530, 2, None, True)

    def _test_should_log_event(
        self,
        last_bytes_value: int,
        network_num: int,
        short_id: Optional[int],
        expected_to_log: bool,
    ):
        tx_hash = helpers.generate_bytearray(crypto.SHA256_HASH_LEN)
        struct.pack_into(">H", tx_hash, crypto.SHA256_HASH_LEN - 2, last_bytes_value)

        self.assertEqual(
            expected_to_log,
            tx_stats.should_log_event_for_tx(
                tx_hash,
                network_num,
                short_id
            )
        )
