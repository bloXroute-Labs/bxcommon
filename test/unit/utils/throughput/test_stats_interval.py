import json

from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.test_utils.mocks.mock_node import MockNode
from bxcommon.utils.throughput.direction import Direction
from bxcommon.utils.throughput.stats_interval import StatsInterval
from bxcommon.utils.throughput.throughput_event import ThroughputEvent


class StatsIntervalTests(AbstractTestCase):

    def setUp(self):
        self.stats_interval = StatsInterval(MockNode("localhost", 8888))
        self.inbound_throughput_event1 = ThroughputEvent(Direction.INBOUND, "test_in_msg", 100, "localhost 0000")
        self.inbound_throughput_event2 = ThroughputEvent(Direction.INBOUND, "test_in_msg", 50, "localhost 0000")
        self.inbound_throughput_event3 = ThroughputEvent(Direction.INBOUND, "mock_msg", 60, "localhost 0000")

        self.outbound_throughput_event1 = ThroughputEvent(Direction.OUTBOUND, "test_out_msg", 100, "localhost 0000")
        self.outbound_throughput_event2 = ThroughputEvent(Direction.OUTBOUND, "test_out_msg", 75, "localhost 0000")

    def test_adding_inbound_event(self):
        self.stats_interval.add_throughput_event(self.inbound_throughput_event1)

        peer_stats = self.stats_interval._peer_to_stats[self.inbound_throughput_event1.peer_desc]

        self.assertEqual(self.inbound_throughput_event1.peer_desc, peer_stats.address)
        self.assertEqual(self.inbound_throughput_event1.num_bytes,
                         peer_stats.messages_received[self.inbound_throughput_event1.msg_type].bytes)
        self.assertNotEqual(self.inbound_throughput_event1.num_bytes, peer_stats.messages_sent.bytes)

    def test_adding_outbound_event(self):
        self.stats_interval.add_throughput_event(self.outbound_throughput_event1)

        peer_stats = self.stats_interval._peer_to_stats[self.outbound_throughput_event1.peer_desc]

        self.assertEqual(self.outbound_throughput_event1.peer_desc, peer_stats.address)
        self.assertEqual(self.outbound_throughput_event1.num_bytes, peer_stats.messages_sent.bytes)
        self.assertNotEqual(self.outbound_throughput_event1.num_bytes,
                            peer_stats.messages_received[self.inbound_throughput_event1.num_bytes].bytes)

    def test_get_json_when_no_node_set(self):
        self.stats_interval._node = None

        with self.assertRaises(ValueError):
            self.stats_interval.get_json()

    def test_get_json_for_same_events(self):
        self.stats_interval.add_throughput_event(self.inbound_throughput_event1)
        self.stats_interval.add_throughput_event(self.inbound_throughput_event2)
        self.stats_interval.add_throughput_event(self.outbound_throughput_event1)
        self.stats_interval.add_throughput_event(self.outbound_throughput_event2)

        stats_json = json.loads(self.stats_interval.get_json())

        self.assertEqual(1, len(stats_json["peer_stats"]))
        self.assertEqual(self.inbound_throughput_event1.num_bytes + self.inbound_throughput_event2.num_bytes,
                         stats_json["peer_stats"][0]["messages_received"]["test_in_msg"]["bytes"])
        self.assertEqual(self.outbound_throughput_event1.num_bytes + self.outbound_throughput_event2.num_bytes,
                         stats_json["peer_stats"][0]["messages_sent"]["bytes"])

        self.assertEqual(self.inbound_throughput_event1.num_bytes + self.inbound_throughput_event2.num_bytes,
                         stats_json["total_bytes_received"])
        self.assertEqual(self.outbound_throughput_event1.num_bytes + self.outbound_throughput_event2.num_bytes,
                         stats_json["total_bytes_sent"])

    def test_get_json_for_different_events(self):
        self.stats_interval.add_throughput_event(self.inbound_throughput_event1)
        self.stats_interval.add_throughput_event(self.inbound_throughput_event3)
        self.stats_interval.add_throughput_event(self.outbound_throughput_event1)
        self.stats_interval.add_throughput_event(self.outbound_throughput_event2)

        stats_json = json.loads(self.stats_interval.get_json())

        self.assertEqual(1, len(stats_json["peer_stats"]))
        self.assertEqual(self.inbound_throughput_event1.num_bytes,
                         stats_json["peer_stats"][0]["messages_received"]["test_in_msg"]["bytes"])
        self.assertEqual(self.inbound_throughput_event3.num_bytes,
                         stats_json["peer_stats"][0]["messages_received"]["mock_msg"]["bytes"])
        self.assertEqual(self.outbound_throughput_event1.num_bytes + self.outbound_throughput_event2.num_bytes,
                         stats_json["peer_stats"][0]["messages_sent"]["bytes"])

        self.assertEqual(self.inbound_throughput_event1.num_bytes + self.inbound_throughput_event3.num_bytes,
                         stats_json["total_bytes_received"])
        self.assertEqual(self.outbound_throughput_event1.num_bytes + self.outbound_throughput_event2.num_bytes,
                         stats_json["total_bytes_sent"])
