import dataclasses
import functools

from dataclasses import dataclass
from collections import defaultdict
from typing import Optional, Union, Dict, Type, Any, TYPE_CHECKING

from prometheus_client import Counter

from bxcommon import constants
from bxcommon.network.network_direction import NetworkDirection
from bxcommon.utils.stats.measurement_type import MeasurementType
from bxcommon.utils.stats.peer_stats import PeerStats
from bxcommon.utils.stats.statistics_service import StatisticsService, StatsIntervalData
from bxutils import logging
from bxutils.logging.log_record_type import LogRecordType

logger = logging.get_logger(LogRecordType.Throughput, __name__)

if TYPE_CHECKING:
    # noinspection PyUnresolvedReferences
    # pylint: disable=ungrouped-imports,cyclic-import
    from bxcommon.connections.abstract_node import AbstractNode


bytes_received = Counter("bytes_received", "Number of bytes received from all connections")
bytes_sent = Counter("bytes_sent", "Number of bytes sent on all connections")


@dataclass
class ThroughputIntervalData(StatsIntervalData):
    total_in: int = 0
    total_out: int = 0
    peer_to_stats: Dict[str, PeerStats] = dataclasses.field(
        default_factory=functools.partial(defaultdict, PeerStats)
    )


class ThroughputStatistics(StatisticsService[ThroughputIntervalData, "AbstractNode"]):
    def __init__(
        self,
        interval=constants.THROUGHPUT_STATS_INTERVAL_S,
        look_back=constants.THROUGHPUT_STATS_LOOK_BACK,
    ) -> None:
        super(ThroughputStatistics, self).__init__(
            "ThroughputStats", interval, look_back, reset=True, stat_logger=logger
        )

    def get_interval_data_class(self) -> Type[ThroughputIntervalData]:
        return ThroughputIntervalData

    def add_event(
        self,
        direction: NetworkDirection,
        msg_type: str,
        msg_size: int,
        peer_desc: str,
        peer_id: Optional[str] = None,
    ) -> None:
        peer_stats = self.interval_data.peer_to_stats[peer_desc]
        peer_stats.address = peer_desc
        if peer_id is not None:
            peer_stats.peer_id = peer_id

        if direction == NetworkDirection.INBOUND:
            peer_stats.messages_received[msg_type].bytes += msg_size
            peer_stats.messages_received[msg_type].count += 1
            peer_stats.peer_total_received += msg_size
            self.interval_data.total_in += msg_size
            bytes_received.inc(msg_size)
        else:
            peer_stats.messages_sent.bytes += msg_size
            peer_stats.messages_sent.count += 1
            peer_stats.peer_total_sent += msg_size
            self.interval_data.total_out += msg_size
            bytes_sent.inc(msg_size)

    def add_measurement(
        self,
        peer_desc: str,
        measure_type: MeasurementType,
        measure_value: Union[int, float],
        peer_id: Optional[str] = None,
    ) -> None:
        if peer_id is not None:
            peer_stats = self.interval_data.peer_to_stats[peer_desc]
            peer_stats.peer_id = peer_id
        else:
            peer_stats = self.interval_data.peer_to_stats[peer_desc]
        peer_stats.address = peer_desc

        if measure_type is MeasurementType.PING:
            peer_stats.ping_max = max(peer_stats.ping_max, measure_value)
        elif measure_type is MeasurementType.PING_INCOMING:
            peer_stats.ping_incoming_max = max(peer_stats.ping_incoming_max, measure_value)
        elif measure_type is MeasurementType.PING_OUTGOING:
            peer_stats.ping_outgoing_max = max(peer_stats.ping_outgoing_max, measure_value)

        else:
            raise ValueError(f"Unexpected throughput measurement: {measure_type}={measure_value}")

    def get_info(self) -> Dict[str, Any]:
        node = self.node
        assert node is not None

        node_peers = []
        for conn in node.connection_pool:
            node_peers.append(
                {
                    "peer_address": "%s:%d" % (conn.peer_ip, conn.peer_port),
                    "peer_id": conn.peer_id,
                    "output_buffer_length": conn.get_backlog_size(),
                }
            )

        return {
            "node_id": node.opts.node_id,
            "node_type": node.NODE_TYPE,
            "node_address": f"{node.opts.external_ip}:{node.opts.external_port}",
            "node_peers": node_peers,
            "total_bytes_received": self.interval_data.total_in,
            "total_bytes_sent": self.interval_data.total_out,
            "peer_stats": list(self.interval_data.peer_to_stats.values()),
            "start_time": self.interval_data.start_time,
            "end_time": self.interval_data.end_time,
        }


throughput_statistics = ThroughputStatistics()
