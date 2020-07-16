from datetime import datetime
from threading import active_count
from typing import Type, Any, Dict, TYPE_CHECKING

from bxcommon.constants import INFO_STATS_INTERVAL_S
from bxcommon.utils.stats.statistics_service import StatisticsService, StatsIntervalData
from bxutils import logging
from bxutils.logging.log_record_type import LogRecordType

if TYPE_CHECKING:
    # noinspection PyUnresolvedReferences
    # pylint: disable=ungrouped-imports,cyclic-import
    from bxcommon.connections.abstract_node import AbstractNode


class NodeInfo(StatisticsService[StatsIntervalData, "AbstractNode"]):
    def __init__(self, interval: int = 0) -> None:
        super(NodeInfo, self).__init__(
            "NodeInfo",
            interval=interval,
            look_back=0,
            reset=False,
            stat_logger=logging.get_logger(LogRecordType.NodeInfo, __name__),
        )

    def get_interval_data_class(self) -> Type[StatsIntervalData]:
        return StatsIntervalData

    def get_info(self) -> Dict[str, Any]:
        node = self.node
        assert node is not None
        payload = dict(node.opts.__dict__)
        payload["current_time"] = datetime.utcnow()
        payload["node_peers"] = {
            connection_type: len(connections)
            for (
                connection_type,
                connections,
            ) in node.connection_pool.by_connection_type.items()
        }
        payload["threads"] = active_count()

        return payload


node_info_statistics = NodeInfo(interval=INFO_STATS_INTERVAL_S)
