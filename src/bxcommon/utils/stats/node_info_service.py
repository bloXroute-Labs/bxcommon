from datetime import datetime
from threading import active_count
from bxcommon.utils.stats.statistics_service import StatisticsService
from bxcommon.constants import INFO_STATS_INTERVAL_S
from bxutils.logging.log_record_type import LogRecordType
from bxutils import logging


class NodeInfo(StatisticsService):
    def __init__(self, interval=0):
        super(NodeInfo, self).__init__("NodeInfo", interval=interval, look_back=0, reset=False,
                                       logger=logging.get_logger(LogRecordType.NodeInfo))

    def get_info(self):
        payload = dict(self.node.opts.__dict__)
        payload["current_time"] = datetime.utcnow()
        payload["node_peers"] = {connection_type: len(connections) for (connection_type, connections)
                                 in self.node.connection_pool.by_connection_type.items()}
        payload["threads"] = active_count()

        return payload


node_info_statistics = NodeInfo(interval=INFO_STATS_INTERVAL_S)
