import time
import unittest

from bxcommon.models.outbound_peer_model import OutboundPeerModel
from bxcommon import constants
from bxcommon.utils import network_latency
from bxcommon.utils.ping_latency import NodeLatencyInfo


class NetworkLatencyTests(unittest.TestCase):
    def test_get_best_relay(self):
        relays = [OutboundPeerModel("34.227.149.148", node_id="0"), OutboundPeerModel("35.198.90.230", node_id="1"),
                  OutboundPeerModel("52.221.211.38", node_id="2"), OutboundPeerModel("34.245.23.125", node_id="3"),
                  OutboundPeerModel("34.238.245.201", node_id="4")]
        sorted_relays_ping_latency = [NodeLatencyInfo(relays[4], 100), NodeLatencyInfo(relays[1], 101),
                                      NodeLatencyInfo(relays[1], 109), NodeLatencyInfo(relays[2], 120),
                                      NodeLatencyInfo(relays[0], 130)]
        best_relay = network_latency._get_best_relay(sorted_relays_ping_latency, relays)
        self.assertEqual("1", best_relay.node.node_id)

    def test_get_best_relay_1(self):
        relays = [OutboundPeerModel("34.227.149.148", node_id="0"), OutboundPeerModel("35.198.90.230", node_id="1"),
                  OutboundPeerModel("52.221.211.38", node_id="2"), OutboundPeerModel("34.245.23.125", node_id="3"),
                  OutboundPeerModel("34.238.245.201", node_id="4")]
        sorted_relays_ping_latency = [NodeLatencyInfo(relays[3], 100), NodeLatencyInfo(relays[1], 101),
                                      NodeLatencyInfo(relays[4], 109), NodeLatencyInfo(relays[2], 120),
                                      NodeLatencyInfo(relays[0], 130)]
        best_relay = network_latency._get_best_relay(sorted_relays_ping_latency, relays)
        self.assertEqual("1", best_relay.node.node_id)

    def test_get_best_relay_sorted_relays(self):
        relays = [OutboundPeerModel("34.227.149.148", node_id="0"), OutboundPeerModel("35.198.90.230", node_id="1"),
                  OutboundPeerModel("52.221.211.38", node_id="2"), OutboundPeerModel("34.245.23.125", node_id="3"),
                  OutboundPeerModel("34.238.245.201", node_id="4")]
        sorted_relays_ping_latency = [NodeLatencyInfo(relays[0], 100), NodeLatencyInfo(relays[1], 101),
                                      NodeLatencyInfo(relays[2], 109), NodeLatencyInfo(relays[3], 120),
                                      NodeLatencyInfo(relays[4], 130)]
        best_relay = network_latency._get_best_relay(sorted_relays_ping_latency, relays)
        self.assertEqual("0", best_relay.node.node_id)

    def test_get_best_relay_one_relay(self):
        relays = [OutboundPeerModel("34.227.149.148", node_id="0")]
        sorted_relays_ping_latency = [NodeLatencyInfo(relays[0], 100)]
        best_relay = network_latency._get_best_relay(sorted_relays_ping_latency, relays)
        self.assertEqual("0", best_relay.node.node_id)

    def test_get_ping_latencies_in_threads(self):
        relays = [OutboundPeerModel("34.227.149.148", node_id="0"), OutboundPeerModel("35.198.90.230", node_id="1"),
                  OutboundPeerModel("52.221.211.38", node_id="2"), OutboundPeerModel("34.245.23.125", node_id="3"),
                  OutboundPeerModel("34.238.245.201", node_id="4")]
        start = time.time()
        network_latency.get_best_relay_by_ping_latency(relays)
        end = time.time() - start
        self.assertTrue(end < constants.PING_TIMEOUT_S + 1)

    def test_get_ping_latency(self):
        relay = OutboundPeerModel("34.227.149.148", node_id="0")
        start = time.time()
        network_latency.get_best_relay_by_ping_latency([relay])
        end = time.time() - start
        self.assertTrue(end < constants.PING_TIMEOUT_S + 1)

