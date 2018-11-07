from collections import deque

from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.test_utils.mocks.mock_node import MockNode
from bxcommon.utils.throughput.direction import Direction
from bxcommon.utils.throughput.stats_interval import StatsInterval
from bxcommon.utils.throughput.throughput_service import throughput_service


class ThroughputServiceTests(AbstractTestCase):

    def setUp(self):
        throughput_service.set_node(MockNode("localhost", 8888))

    def tearDown(self):
        throughput_service.stats_interval = None
        throughput_service.throughput_stats = deque()

    def test_initialization(self):
        self.assertEqual(MockNode, type(throughput_service.node))
        self.assertEqual(StatsInterval, type(throughput_service.stats_interval))

    def test_add_throughput_event(self):
        self.assertEqual(0, len(throughput_service.stats_interval._peer_to_stats))
        throughput_service.add_event(Direction.INBOUND, "mock_msg", 100, "localhost 0000")
        self.assertEqual(1, len(throughput_service.stats_interval._peer_to_stats))

    def test_flush_stats_less_than_max_look_back(self):
        throughput_service.add_event(Direction.INBOUND, "mock_msg", 100, "localhost 0000")
        self.assertEqual(0, len(throughput_service.throughput_stats))
        throughput_service.flush_stats()
        self.assertEqual(1, len(throughput_service.throughput_stats))
        self.assertEqual(0, len(throughput_service.stats_interval._peer_to_stats))

    def test_flush_stats_greater_than_max_look_back(self):
        for _ in range(0, 10):
            throughput_service.add_event(Direction.INBOUND, "mock_msg", 100, "localhost 0000")
            throughput_service.add_event(Direction.OUTBOUND, None, 50, "localhost 0000")
            throughput_service.flush_stats()

        self.assertEqual(10, len(throughput_service.throughput_stats))

        for _ in range(0, 5):
            throughput_service.add_event(Direction.INBOUND, "mock_msg", 100, "localhost 0000")
            throughput_service.add_event(Direction.OUTBOUND, None, 50, "localhost 0000")
            throughput_service.flush_stats()

        self.assertEqual(10, len(throughput_service.throughput_stats))
