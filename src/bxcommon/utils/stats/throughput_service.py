from collections import defaultdict
from typing import Optional, Union

from bxcommon import constants
from bxcommon.network.network_direction import NetworkDirection
from bxcommon.utils.stats.measurement_type import MeasurementType
from bxcommon.utils.stats.peer_stats import PeerStats
from bxcommon.utils.stats.statistics_service import StatisticsService, \
    StatsIntervalData
from bxutils import logging
from bxutils.logging.log_record_type import LogRecordType

logger = logging.get_logger(LogRecordType.Throughput, __name__)


class ThroughputIntervalData(StatsIntervalData):
    __slots__ = ["total_in", "total_out", "peer_to_stats"]

    def __init__(self, *args, **kwargs):
        super(ThroughputIntervalData, self).__init__(*args, **kwargs)
        self.total_in = 0
        self.total_out = 0
        self.peer_to_stats = defaultdict(PeerStats)


class ThroughputStatistics(StatisticsService):
    INTERVAL_DATA_CLASS = ThroughputIntervalData

    def __init__(self, interval=constants.THROUGHPUT_STATS_INTERVAL_S, look_back=constants.THROUGHPUT_STATS_LOOK_BACK):
        super(ThroughputStatistics, self).__init__("ThroughputStats", interval, look_back, reset=True, logger=logger)

    def add_event(self,
                  direction: NetworkDirection,
                  msg_type: str,
                  msg_size: int,
                  peer_desc: str,
                  peer_id: Optional[str] = None):
        peer_stats = self.interval_data.peer_to_stats[peer_desc]
        peer_stats.address = peer_desc
        if peer_id is not None:
            peer_stats.peer_id = peer_id

        if direction == NetworkDirection.INBOUND:
            peer_stats.messages_received[msg_type].bytes += msg_size
            peer_stats.messages_received[msg_type].count += 1
            peer_stats.peer_total_received += msg_size
            self.interval_data.total_in += msg_size
        else:
            peer_stats.messages_sent.bytes += msg_size
            peer_stats.messages_sent.count += 1
            peer_stats.peer_total_sent += msg_size
            self.interval_data.total_out += msg_size

    def add_throughput_event(self, throughput_event):
        return self.add_event(direction=throughput_event.direction, msg_type=throughput_event.msg_type,
                              msg_size=throughput_event.msg_size, peer_desc=throughput_event.peer_desc)

    def add_measurement(self,
                        peer_desc: str,
                        measure_type: MeasurementType,
                        measure_value: Union[int, float],
                        peer_id: Optional[str] = None
                        ):
        peer_stats = self.interval_data.peer_to_stats[peer_desc]
        peer_stats.address = peer_desc
        if peer_id is not None:
            peer_stats.peer_id = peer_id

        if measure_type is MeasurementType.PING:
            if peer_stats.ping_max is None:
                peer_stats.ping_max = measure_value
            else:
                peer_stats.ping_max = max(peer_stats.ping_max, measure_value)
        else:
            # TODO: should be assertion that this should not happen
            logger.error("Unexpected throughput measurement: {}={}".format(measure_type, measure_value))

    def get_info(self):
        if self.node is None:
            raise ValueError
        payload = dict(
            node_id=self.interval_data.node.opts.node_id,
            node_type=self.interval_data.node.NODE_TYPE,
            node_address="%s:%d" % (
                self.interval_data.node.opts.external_ip, self.interval_data.node.opts.external_port),
            node_peers=[],
            total_bytes_received=self.interval_data.total_in,
            total_bytes_sent=self.interval_data.total_out,
            peer_stats=[],
            start_time=self.interval_data.start_time,
            end_time=self.interval_data.end_time,
        )
        for conn in self.interval_data.node.connection_pool:
            payload["node_peers"].append(
                {
                    "peer_address": "%s:%d" % (conn.peer_ip, conn.peer_port),
                    "peer_id": conn.peer_id,
                    "output_buffer_length": conn.get_backlog_size()
                 }
            )
        payload["peer_stats"] = list(self.interval_data.peer_to_stats.values())
        return payload


throughput_statistics = ThroughputStatistics()
