from datetime import datetime
from bxcommon.utils.stats.statistics_service import StatisticsService
from bxcommon.constants import INFO_STATS_INTERVAL_S


class NodeInfo(StatisticsService):
    def __init__(self, interval=0):
        super(NodeInfo, self).__init__("NodeInfo", interval=interval, look_back=0, reset=False)

    def get_info(self):
        payload = dict(self.node.opts.__dict__)
        payload["current_time"] = datetime.utcnow()
        payload["node_peers"] = {connection_type: len(connections) for (connection_type, connections)
                                 in self.node.connection_pool.by_connection_type.items()}

        return payload


node_info_statistics = NodeInfo(interval=INFO_STATS_INTERVAL_S)
