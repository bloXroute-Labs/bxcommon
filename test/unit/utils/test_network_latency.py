import time
import unittest

from mock import patch

from bxcommon import constants
from bxcommon.models.outbound_peer_model import OutboundPeerModel
from bxcommon.utils import network_latency
from bxcommon.utils.ping_latency import NodeLatencyInfo


class NetworkLatencyTests(unittest.TestCase):
    def test_get_best_relay(self):
        relays = [
            OutboundPeerModel("34.227.149.148", 1609, node_id="0", attributes={"country": "China"}),
            OutboundPeerModel("35.198.90.230", 1609, node_id="1", attributes={"country": "China"}),
            OutboundPeerModel("52.221.211.38", 1609, node_id="2", attributes={"country": "China"}),
            OutboundPeerModel("34.245.23.125", 1609, node_id="3", attributes={"country": "China"}),
            OutboundPeerModel("34.238.245.201", 1609, node_id="4", attributes={"country": "China"}),
        ]

        sorted_relays_ping_latency = [
            NodeLatencyInfo(relays[4], 100),
            NodeLatencyInfo(relays[1], 101),
            NodeLatencyInfo(relays[3], 109),
            NodeLatencyInfo(relays[2], 120),
            NodeLatencyInfo(relays[0], 130),
        ]
        best_relays = network_latency._get_best_relay_latencies_one_per_country(
            sorted_relays_ping_latency, relays, 1
        )
        self.assertEqual(1, len(best_relays))
        self.assertEqual("1", best_relays[0].node.node_id)

    def test_get_best_relay_multiple(self):
        relays = [
            OutboundPeerModel("34.227.149.148", 1609, node_id="0", attributes={"country": "China"}),
            OutboundPeerModel("35.198.90.230", 1609, node_id="1", attributes={"country": "China"}),
            OutboundPeerModel("52.221.211.38", 1609, node_id="2", attributes={"country": "China"}),
            OutboundPeerModel("34.245.23.125", 1609, node_id="3", attributes={"country": "EU"}),
            OutboundPeerModel("34.238.245.201", 1609, node_id="4", attributes={"country": "EU"}),
        ]

        sorted_relays_ping_latency = [
            NodeLatencyInfo(relays[4], 100),
            NodeLatencyInfo(relays[1], 101),
            NodeLatencyInfo(relays[3], 109),
            NodeLatencyInfo(relays[2], 120),
            NodeLatencyInfo(relays[0], 130),
        ]
        best_relays = network_latency._get_best_relay_latencies_one_per_country(
            sorted_relays_ping_latency, relays, 2
        )
        self.assertEqual(2, len(best_relays))
        self.assertEqual("1", best_relays[0].node.node_id)
        self.assertEqual("3", best_relays[1].node.node_id)

    def test_get_best_relay_1(self):
        relays = [
            OutboundPeerModel("34.227.149.148", 1609, node_id="0", attributes={"country": "China"}),
            OutboundPeerModel("35.198.90.230", 1609, node_id="1", attributes={"country": "China"}),
            OutboundPeerModel("52.221.211.38", 1609, node_id="2", attributes={"country": "China"}),
            OutboundPeerModel("34.245.23.125", 1609, node_id="3", attributes={"country": "China"}),
            OutboundPeerModel("34.238.245.201", 1609, node_id="4", attributes={"country": "China"}),
        ]

        sorted_relays_ping_latency = [
            NodeLatencyInfo(relays[3], 100),
            NodeLatencyInfo(relays[1], 101),
            NodeLatencyInfo(relays[4], 109),
            NodeLatencyInfo(relays[2], 120),
            NodeLatencyInfo(relays[0], 130),
        ]
        best_relays = network_latency._get_best_relay_latencies_one_per_country(
            sorted_relays_ping_latency, relays, 1
        )

        self.assertEqual(1, len(best_relays))
        self.assertEqual("1", best_relays[0].node.node_id)

    def test_get_best_relay_sorted_relays(self):
        relays = [
            OutboundPeerModel("34.227.149.148", 1609, node_id="0", attributes={"country": "China"}),
            OutboundPeerModel("35.198.90.230", 1609, node_id="1", attributes={"country": "China"}),
            OutboundPeerModel("52.221.211.38", 1609, node_id="2", attributes={"country": "China"}),
            OutboundPeerModel("34.245.23.125", 1609, node_id="3", attributes={"country": "China"}),
            OutboundPeerModel("34.238.245.201", 1609, node_id="4", attributes={"country": "China"}),
        ]
        sorted_relays_ping_latency = [
            NodeLatencyInfo(relays[0], 100),
            NodeLatencyInfo(relays[1], 101),
            NodeLatencyInfo(relays[2], 109),
            NodeLatencyInfo(relays[3], 120),
            NodeLatencyInfo(relays[4], 130),
        ]
        best_relay = network_latency._get_best_relay_latencies_one_per_country(
            sorted_relays_ping_latency, relays, 1
        )
        self.assertEqual("0", best_relay[0].node.node_id)

    def test_get_best_relay_one_relay(self):
        relays = [OutboundPeerModel("34.227.149.148", 1609, node_id="0", attributes={"country": "China"})]
        sorted_relays_ping_latency = [NodeLatencyInfo(relays[0], 100)]
        best_relays = network_latency._get_best_relay_latencies_one_per_country(
            sorted_relays_ping_latency, relays, 1
        )
        self.assertEqual(1, len(best_relays))
        self.assertEqual("0", best_relays[0].node.node_id)

    def test_get_best_relay_less_relays(self):
        relays = [OutboundPeerModel("34.227.149.148", 1609, node_id="0", attributes={"country": "China"})]
        sorted_relays_ping_latency = [NodeLatencyInfo(relays[0], 100)]
        best_relays = network_latency._get_best_relay_latencies_one_per_country(
            sorted_relays_ping_latency, relays, 2
        )
        self.assertEqual(1, len(best_relays))
        self.assertEqual("0", best_relays[0].node.node_id)

    def test_get_ping_latencies_in_threads(self):
        relays = [
            OutboundPeerModel("34.227.149.148", 1609, node_id="0", attributes={"country": "China"}),
            OutboundPeerModel("35.198.90.230", 1609, node_id="1", attributes={"country": "China"}),
            OutboundPeerModel("52.221.211.38", 1609, node_id="2", attributes={"country": "China"}),
            OutboundPeerModel("34.245.23.125", 1609, node_id="3", attributes={"country": "China"}),
            OutboundPeerModel("34.238.245.201", 1609, node_id="4", attributes={"country": "China"}),
        ]
        start = time.time()
        network_latency.get_best_relays_by_ping_latency_one_per_country(relays, 1)
        end = time.time() - start
        self.assertTrue(end < constants.PING_TIMEOUT_S + 1)

    @patch("bxcommon.utils.ping_latency.get_ping_latencies")
    def test_get_ping_latencies_one_country(self, mock_get_ping_latencies):
        relays = [
            OutboundPeerModel("34.227.149.148", 1609, node_id="0", attributes={"country": "China"}),
            OutboundPeerModel("35.198.90.230", 1609, node_id="1", attributes={"country": "China"}),
            OutboundPeerModel("52.221.211.38", 1609, node_id="2", attributes={"country": "China"}),
            OutboundPeerModel("34.245.23.125", 1609, node_id="3", attributes={"country": "EU"}),
            OutboundPeerModel("34.238.245.201", 1609, node_id="4", attributes={"country": "EU"}),
        ]

        mock_get_ping_latencies.return_value = [
            NodeLatencyInfo(relays[4], 100),
            NodeLatencyInfo(relays[1], 101),
            NodeLatencyInfo(relays[3], 109),
            NodeLatencyInfo(relays[2], 120),
            NodeLatencyInfo(relays[0], 130),
        ]
        best_relays = network_latency.get_best_relays_by_ping_latency_one_per_country(relays, 1)
        self.assertEqual(1, len(best_relays))
        self.assertEqual("1", best_relays[0].node_id)

    @patch("bxcommon.utils.ping_latency.get_ping_latencies")
    def test_get_ping_latencies_multiple_countries(self, mock_get_ping_latencies):
        relays = [
            OutboundPeerModel("34.227.149.148", 1609, node_id="0", attributes={"country": "China"}),
            OutboundPeerModel("35.198.90.230", 1609, node_id="1", attributes={"country": "China"}),
            OutboundPeerModel("52.221.211.38", 1609, node_id="2", attributes={"country": "China"}),
            OutboundPeerModel("34.245.23.125", 1609, node_id="3", attributes={"country": "EU"}),
            OutboundPeerModel("34.238.245.201", 1609, node_id="4", attributes={"country": "EU"}),
        ]

        mock_get_ping_latencies.return_value = [
            NodeLatencyInfo(relays[4], 100),
            NodeLatencyInfo(relays[1], 101),
            NodeLatencyInfo(relays[3], 109),
            NodeLatencyInfo(relays[2], 120),
            NodeLatencyInfo(relays[0], 130),
        ]
        best_relays = network_latency.get_best_relays_by_ping_latency_one_per_country(relays, 2)
        self.assertEqual(2, len(best_relays))
        self.assertEqual("1", best_relays[0].node_id)
        self.assertEqual("3", best_relays[1].node_id)

    @patch("bxcommon.utils.ping_latency.get_ping_latencies")
    def test_get_ping_latencies_first_peer_optimal(self, mock_get_ping_latencies):
        relays = [
            OutboundPeerModel("34.227.149.148", 1609, node_id="0", attributes={"country": "China"}),
            OutboundPeerModel("35.198.90.230", 1609, node_id="1", attributes={"country": "China"}),
            OutboundPeerModel("52.221.211.38", 1609, node_id="2", attributes={"country": "China"}),
            OutboundPeerModel("34.245.23.125", 1609, node_id="3", attributes={"country": "EU"}),
            OutboundPeerModel("34.238.245.201", 1609, node_id="4", attributes={"country": "EU"}),
        ]

        mock_get_ping_latencies.return_value = [
            NodeLatencyInfo(relays[4], 100),
            NodeLatencyInfo(relays[1], 101),
            NodeLatencyInfo(relays[3], 109),
            NodeLatencyInfo(relays[2], 120),
            NodeLatencyInfo(relays[0], 103),
        ]
        best_relays = network_latency.get_best_relays_by_ping_latency_one_per_country(relays, 2)
        self.assertEqual(2, len(best_relays))
        self.assertEqual("0", best_relays[0].node_id)
        self.assertEqual("3", best_relays[1].node_id)

    @patch("bxcommon.utils.ping_latency.get_ping_latencies")
    @patch("bxcommon.utils.ping_latency.get_ping_latency")
    def test_get_ping_latencies_first_peer_optimal_from_the_same_country_as_fastest(
        self, mock_get_ping_latency, mock_get_ping_latencies
    ):
        relays = [
            OutboundPeerModel("34.227.149.148", 1609, node_id="0", attributes={"country": "China"}),
            OutboundPeerModel("35.198.90.230", 1609, node_id="1", attributes={"country": "China"}),
            OutboundPeerModel("52.221.211.38", 1609, node_id="2", attributes={"country": "China"}),
            OutboundPeerModel("34.245.23.125", 1609, node_id="3", attributes={"country": "EU"}),
            OutboundPeerModel("34.238.245.201", 1609, node_id="4", attributes={"country": "EU"}),
        ]

        mock_get_ping_latencies.return_value = [
            NodeLatencyInfo(relays[4], 100),
            NodeLatencyInfo(relays[1], 0),
            NodeLatencyInfo(relays[3], 109),
            NodeLatencyInfo(relays[2], 10),
            NodeLatencyInfo(relays[0], 1),
        ]
        mock_get_ping_latency.return_value = NodeLatencyInfo(relays[0], 1)
        best_relays = network_latency.get_best_relays_by_ping_latency_one_per_country(relays, 2)
        self.assertEqual(2, len(best_relays))
        self.assertEqual("0", best_relays[0].node_id)
        self.assertEqual("3", best_relays[1].node_id)

    @patch("bxcommon.utils.ping_latency.get_ping_latencies")
    def test_get_ping_latencies_current_relay_within_threshold_of_fastest(
        self, mock_get_ping_latencies
    ):
        current_relay = OutboundPeerModel("52.221.211.38", 1609, node_id="2", attributes={"country": "EU"})
        fastest_relay = OutboundPeerModel("35.198.90.230", 1609, node_id="1", attributes={"country": "EU"})
        first_recommended_relay = OutboundPeerModel("34.227.149.148", 1609, node_id="0", attributes={"country": "EU"})
        self.peer_relays = set()
        self.peer_relays.add(current_relay)

        relays = [
            first_recommended_relay,
            fastest_relay,
            current_relay,
            OutboundPeerModel("34.245.23.125", 1609, node_id="3", attributes={"country": "China"}),
            OutboundPeerModel("34.238.245.201", 1609, node_id="4", attributes={"country": "China"}),
        ]

        mock_get_ping_latencies.return_value = [
            NodeLatencyInfo(relays[4], 100),
            NodeLatencyInfo(fastest_relay, 8),
            NodeLatencyInfo(relays[3], 109),
            NodeLatencyInfo(current_relay, 10),
            NodeLatencyInfo(first_recommended_relay, 9),
        ]
        best_relays = network_latency.get_best_relays_by_ping_latency_one_per_country(relays, 2, self.peer_relays)
        self.assertEqual(2, len(best_relays))
        self.assertEqual("2", best_relays[0].node_id)
        self.assertEqual("3", best_relays[1].node_id)

    def test_get_ping_latency(self):
        relay = OutboundPeerModel("34.227.149.148", 1609, node_id="0", attributes={"country": "China"})
        start = time.time()
        network_latency.get_best_relays_by_ping_latency_one_per_country([relay], 1)
        end = time.time() - start
        self.assertTrue(end < constants.PING_TIMEOUT_S + 1)
