import json
import time
from collections import defaultdict

from bxcommon.utils.class_json_encoder import ClassJsonEncoder
from bxcommon.utils.throughput.direction import Direction
from bxcommon.utils.throughput.peer_stats import PeerStats
from bxcommon.utils.throughput.throughput_payload import ThroughputPayload


class StatsInterval(object):

    def __init__(self, node):
        self._start_time = time.time()
        self._total_in = 0
        self._total_out = 0
        self._node = node
        self._peer_to_stats = defaultdict(PeerStats)

    def add_throughput_event(self, throughput_event):
        peer_stats = self._peer_to_stats[throughput_event.peer_desc]
        peer_stats.address = throughput_event.peer_desc

        if throughput_event.direction is Direction.INBOUND:
            peer_stats.messages_received[throughput_event.msg_type].bytes += throughput_event.num_bytes
            peer_stats.peer_total_received += throughput_event.num_bytes
            self._total_in += throughput_event.num_bytes
        else:
            peer_stats.messages_sent.bytes += throughput_event.num_bytes
            peer_stats.peer_total_sent += throughput_event.num_bytes
            self._total_out += throughput_event.num_bytes

    def get_json(self):
        if self._node is None:
            raise ValueError("Node must be set for stats service.")

        payload = ThroughputPayload(self._start_time, time.time())
        payload.node_type = self._node.node_type
        payload.node_address = "%s:%d" % (self._node.opts.external_ip, self._node.opts.external_port)
        payload.total_bytes_received = self._total_in
        payload.total_bytes_sent = self._total_out

        for conn in self._node.connection_pool:
            payload.node_peers.append(
                {"peer_address": "%s:%d" % (conn.peer_ip, conn.peer_port)})

        payload.peer_stats = self._peer_to_stats.values()

        return json.dumps(payload, cls=ClassJsonEncoder)
