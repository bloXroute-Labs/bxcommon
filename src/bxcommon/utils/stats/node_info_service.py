from bxcommon.utils.stats.statistics_service import StatisticsService
from bxcommon.constants import INFO_STATS_INTERVAL


class NodeInfo(StatisticsService):
    def __init__(self, interval=0):
        super(NodeInfo, self).__init__(interval=interval, look_back=0, reset=False)
        self.name = "NodeInfo"

    def get_info(self):
        payload = dict(
            current_time=self.interval_data.end_time,
            idx=self.node.idx,
            bloxroute_version=self.node.opts.__dict__.get("bloxroute_version"),
            external_ip=self.node.opts.external_ip,
            external_port=self.node.opts.external_port,
            network=self.node.opts.network,
            node_id=self.node.opts.node_id,
            node_type=self.node.opts.node_type,
            sdn_socket_url=self.node.opts.__dict__.get("sdn_socket_ip"),
            sdn_socket_port=self.node.opts.__dict__.get("sdn_socket_port"),
            sdn_url=self.node.opts.sdn_url,
            sid_start=self.node.opts.sid_start,
            sid_end=self.node.opts.sid_end,
            sid_expire_time=self.node.opts.sid_expire_time,
            source_version=self.node.opts.source_version,
            node_peers=self.node.opts.outbound_peers,
            protocol_version=self.node.opts.__dict__.get("protocol_version"),
            blockchain_network=self.node.opts.__dict__.get("blockchain_network"),
            blockchain_protocol=self.node.opts.__dict__.get("blockchain_protocol"),
        )

        return payload


node_info_statistics = NodeInfo(interval=INFO_STATS_INTERVAL)
