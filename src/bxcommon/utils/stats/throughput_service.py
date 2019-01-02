from collections import defaultdict

from bxcommon.utils.stats.statistics_service import StatisticsService
from bxcommon.constants import THROUGHPUT_STATS_INTERVAL
from bxcommon.utils.stats.peer_stats import PeerStats
from bxcommon.utils.stats.direction import Direction


class ThroughputStatistics(StatisticsService):
    def __init__(self, interval=0):
        super(ThroughputStatistics, self).__init__(interval=interval, look_back=5, reset=True)
        self.name = "ThroughputStats"

    def create_interval_data_object(self):
        super(ThroughputStatistics, self).create_interval_data_object()
        self.interval_data.total_in = 0
        self.interval_data.total_out = 0
        self.interval_data.peer_to_stats = defaultdict(PeerStats)

    def add_event(self, direction, msg_type, msg_size, peer_desc):
        peer_stats = self.interval_data.peer_to_stats[peer_desc]
        peer_stats.address = peer_desc

        if direction is Direction.INBOUND:
            peer_stats.messages_received[msg_type].bytes += msg_size
            peer_stats.peer_total_received += msg_size
            self.interval_data.total_in += msg_size
        else:
            peer_stats.messages_sent.bytes += msg_size
            peer_stats.peer_total_sent += msg_size
            self.interval_data.total_out += msg_size

    def add_throughput_event(self, throughput_event):
        return self.add_event(direction=throughput_event.direction, msg_type=throughput_event.msg_type,
                              msg_size=throughput_event.msg_size, peer_desc=throughput_event.peer_desc)

    def get_info(self):
        if self.node is None:
            raise ValueError
        payload = dict(
            node_id=self.interval_data.node.opts.node_id,
            node_type=self.interval_data.node.NODE_TYPE,
            node_address="%s:%d" % (self.interval_data.node.opts.external_ip, self.interval_data.node.opts.external_port),
            node_peers=[],
            total_bytes_received=self.interval_data.total_in,
            total_bytes_sent=self.interval_data.total_out,
            peer_stats=[],
            start_time=self.interval_data.start_time,
            end_time=self.interval_data.end_time,
        )
        for conn in self.interval_data.node.connection_pool:
            payload["node_peers"].append(
                {"peer_address": "%s:%d" % (conn.peer_ip, conn.peer_port)})
        payload["peer_stats"] = self.interval_data.peer_to_stats.values()
        return payload


throughput_statistics = ThroughputStatistics(interval=THROUGHPUT_STATS_INTERVAL)
