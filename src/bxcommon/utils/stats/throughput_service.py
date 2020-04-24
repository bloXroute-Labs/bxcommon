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


class ThroughputIntervalData(StatsIntervalData):
    total_in: int
    total_out: int
    peer_to_stats: Dict[str, PeerStats]

    def __init__(self, *args, **kwargs):
        super(ThroughputIntervalData, self).__init__(*args, **kwargs)
        self.total_in = 0
        self.total_out = 0
        self.peer_to_stats = defaultdict(PeerStats)


class ThroughputStatistics(StatisticsService[ThroughputIntervalData, "AbstractNode"]):
    def __init__(
        self,
        interval=constants.THROUGHPUT_STATS_INTERVAL_S,
        look_back=constants.THROUGHPUT_STATS_LOOK_BACK,
    ):
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
        assert self.interval_data is not None
        # pyre-fixme[16]: `Optional` has no attribute `peer_to_stats`.
        peer_stats = self.interval_data.peer_to_stats[peer_desc]
        peer_stats.address = peer_desc
        if peer_id is not None:
            peer_stats.peer_id = peer_id

        if direction == NetworkDirection.INBOUND:
            peer_stats.messages_received[msg_type].bytes += msg_size
            peer_stats.messages_received[msg_type].count += 1
            peer_stats.peer_total_received += msg_size
            # pyre-fixme[16]: `Optional` has no attribute `total_in`.
            self.interval_data.total_in += msg_size
            bytes_received.inc(msg_size)
        else:
            peer_stats.messages_sent.bytes += msg_size
            peer_stats.messages_sent.count += 1
            peer_stats.peer_total_sent += msg_size
            # pyre-fixme[16]: `Optional` has no attribute `total_out`.
            self.interval_data.total_out += msg_size
            bytes_sent.inc(msg_size)

    def add_measurement(
        self,
        peer_desc: str,
        measure_type: MeasurementType,
        measure_value: Union[int, float],
        peer_id: Optional[str] = None,
    ) -> None:
        assert self.interval_data is not None
        # pyre-fixme[16]: `Optional` has no attribute `peer_to_stats`.
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
            raise ValueError(f"Unexpected throughput measurement: {measure_type}={measure_value}")

    def get_info(self) -> Dict[str, Any]:
        assert self.node is not None
        assert self.interval_data is not None

        node_peers = []
        # pyre-fixme[16]: `Optional` has no attribute `connection_pool`.
        for conn in self.node.connection_pool:
            node_peers.append(
                {
                    "peer_address": "%s:%d" % (conn.peer_ip, conn.peer_port),
                    "peer_id": conn.peer_id,
                    "output_buffer_length": conn.get_backlog_size(),
                }
            )

        return {
            # pyre-fixme[16]: `Optional` has no attribute `opts`.
            "node_id": self.node.opts.node_id,
            # pyre-fixme[16]: `Optional` has no attribute `NODE_TYPE`.
            "node_type": self.node.NODE_TYPE,
            "node_address": f"{self.node.opts.external_ip}:{self.node.opts.external_port}",
            "node_peers": node_peers,
            # pyre-fixme[16]: `Optional` has no attribute `total_in`.
            "total_bytes_received": self.interval_data.total_in,
            # pyre-fixme[16]: `Optional` has no attribute `total_out`.
            "total_bytes_sent": self.interval_data.total_out,
            # pyre-fixme[16]: `Optional` has no attribute `peer_to_stats`.
            "peer_stats": list(self.interval_data.peer_to_stats.values()),
            # pyre-fixme[16]: `Optional` has no attribute `start_time`.
            "start_time": self.interval_data.start_time,
            # pyre-fixme[16]: `Optional` has no attribute `end_time`.
            "end_time": self.interval_data.end_time,
        }


throughput_statistics = ThroughputStatistics()
