from collections import deque

from bxcommon.test_utils import helpers
from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.test_utils import helpers
from bxcommon.test_utils.mocks.mock_node import MockNode
from bxcommon.utils.stats.direction import Direction
from bxcommon.utils.stats.measurement_type import MeasurementType
from bxcommon.utils.stats.throughput_service import throughput_statistics
from bxcommon.utils.stats.hooks import add_throughput_event, add_measurement
from bxcommon.utils.stats.throughput_event import ThroughputEvent


class ThroughputServiceTests(AbstractTestCase):

    def setUp(self):
        throughput_statistics.set_node(MockNode(helpers.get_common_opts(8888)))

        self.inbound_throughput_event1 = ThroughputEvent(Direction.INBOUND_MESSAGE, "test_in_msg", 100, "localhost 0000")
        self.inbound_throughput_event2 = ThroughputEvent(Direction.INBOUND_MESSAGE, "test_in_msg", 50, "localhost 0000")
        self.inbound_throughput_event3 = ThroughputEvent(Direction.INBOUND_MESSAGE, "mock_msg", 60, "localhost 0000")

        self.outbound_throughput_event1 = ThroughputEvent(Direction.OUTBOUND, "test_out_msg", 100, "localhost 0000")
        self.outbound_throughput_event2 = ThroughputEvent(Direction.OUTBOUND, "test_out_msg", 75, "localhost 0000")

    def tearDown(self):
        throughput_statistics.interval_data = None
        throughput_statistics.history = deque()

    def test_initialization(self):
        self.assertEqual(MockNode, type(throughput_statistics.node))

    def test_add_throughput_event_peer_count(self):
        self.assertEqual(0, len(throughput_statistics.interval_data.peer_to_stats))
        throughput_statistics.add_event(Direction.INBOUND_MESSAGE, "mock_msg", 100, "localhost 0000")
        self.assertEqual(1, len(throughput_statistics.interval_data.peer_to_stats))

    def test_add_throughput_event_total_bytes(self):
        self.assertEqual(0, throughput_statistics.interval_data.total_in)
        throughput_statistics.add_event(Direction.INBOUND_MESSAGE, "mock_msg", 100, "localhost 0000")
        throughput_statistics.add_event(Direction.INBOUND_MESSAGE, "mock_msg", 100, "localhost 0000")
        self.assertEqual(200, throughput_statistics.interval_data.total_in)

    def test_add_throughput_event_flush(self):
        self.assertEqual(1, throughput_statistics.reset)
        self.assertEqual(0, throughput_statistics.interval_data.total_in)
        throughput_statistics.add_event(Direction.INBOUND_MESSAGE, "mock_msg", 100, "localhost 0000")
        self.assertEqual(100, throughput_statistics.interval_data.total_in)
        throughput_statistics.flush_info()
        self.assertEqual(0, throughput_statistics.interval_data.total_in)


###

    def test_adding_inbound_event(self):
        add_throughput_event(**self.inbound_throughput_event1.__dict__)

        peer_stats = throughput_statistics.interval_data.peer_to_stats[self.inbound_throughput_event1.peer_desc]

        self.assertEqual(self.inbound_throughput_event1.peer_desc, peer_stats.address)
        self.assertEqual(self.inbound_throughput_event1.msg_size,
                         peer_stats.messages_received[self.inbound_throughput_event1.msg_type].bytes)
        self.assertNotEqual(self.inbound_throughput_event1.msg_size, peer_stats.messages_sent.bytes)

    def test_adding_outbound_event(self):
        add_throughput_event(**self.outbound_throughput_event1.__dict__)

        peer_stats = throughput_statistics.interval_data.peer_to_stats[self.inbound_throughput_event1.peer_desc]

        self.assertEqual(self.outbound_throughput_event1.peer_desc, peer_stats.address)
        self.assertEqual(self.outbound_throughput_event1.msg_size, peer_stats.messages_sent.bytes)
        self.assertNotEqual(self.outbound_throughput_event1.msg_size,
                            peer_stats.messages_received[self.inbound_throughput_event1.msg_size].bytes)

    def test_get_json_when_no_node_set(self):
        throughput_statistics.node = None

        with self.assertRaises(ValueError):
            throughput_statistics.get_info()

    def test_get_json_for_same_events(self):
        add_throughput_event(**self.inbound_throughput_event1.__dict__)
        add_throughput_event(**self.inbound_throughput_event2.__dict__)
        add_throughput_event(**self.outbound_throughput_event1.__dict__)
        add_throughput_event(**self.outbound_throughput_event2.__dict__)

        stats_json = throughput_statistics.get_info()

        self.assertEqual(1, len(stats_json["peer_stats"]))
        self.assertEqual(self.inbound_throughput_event1.msg_size + self.inbound_throughput_event2.msg_size,
                         stats_json["peer_stats"][0].messages_received["test_in_msg"].bytes)
        self.assertEqual(self.outbound_throughput_event1.msg_size + self.outbound_throughput_event2.msg_size,
                         stats_json["peer_stats"][0].messages_sent.bytes)

        self.assertEqual(self.inbound_throughput_event1.msg_size + self.inbound_throughput_event2.msg_size,
                         stats_json["total_bytes_received"])
        self.assertEqual(self.outbound_throughput_event1.msg_size + self.outbound_throughput_event2.msg_size,
                         stats_json["total_bytes_sent"])

    def test_get_json_for_different_events(self):
        add_throughput_event(**self.inbound_throughput_event1.__dict__)
        add_throughput_event(**self.inbound_throughput_event3.__dict__)
        add_throughput_event(**self.outbound_throughput_event1.__dict__)
        add_throughput_event(**self.outbound_throughput_event2.__dict__)

        stats_json = throughput_statistics.get_info()

        self.assertEqual(1, len(stats_json["peer_stats"]))
        self.assertEqual(self.inbound_throughput_event1.msg_size,
                         stats_json["peer_stats"][0].messages_received["test_in_msg"].bytes)
        self.assertEqual(self.inbound_throughput_event3.msg_size,
                         stats_json["peer_stats"][0].messages_received["mock_msg"].bytes)
        self.assertEqual(self.outbound_throughput_event1.msg_size + self.outbound_throughput_event2.msg_size,
                         stats_json["peer_stats"][0].messages_sent.bytes)

        self.assertEqual(self.inbound_throughput_event1.msg_size + self.inbound_throughput_event3.msg_size,
                         stats_json["total_bytes_received"])
        self.assertEqual(self.outbound_throughput_event1.msg_size + self.outbound_throughput_event2.msg_size,
                         stats_json["total_bytes_sent"])

    def test_adding_ping_event(self):
        add_throughput_event(Direction.INBOUND_MESSAGE, "ping", 40, "localhost 0000")
        add_measurement("localhost 0000", MeasurementType.PING, 0.1)
        add_measurement("localhost 0000", MeasurementType.PING, 0.3)
        add_measurement("localhost 0000", MeasurementType.PING, 0.2)
        self.assertEqual(throughput_statistics.interval_data.peer_to_stats["localhost 0000"].ping_max, 0.3)
        throughput_statistics.flush_info()
