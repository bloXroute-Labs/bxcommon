from bxcommon.connections.abstract_node import AbstractNode
from bxcommon.connections.node_type import NodeType
from bxcommon.constants import DEFAULT_NETWORK_NUM
from bxcommon.models.blockchain_network_model import BlockchainNetworkModel
from bxcommon.services.transaction_service import TransactionService
from bxcommon.utils.alarm_queue import AlarmQueue


class MockNode(AbstractNode):
    NODE_TYPE = NodeType.RELAY

    def __init__(self, external_ip, external_port):
        mock_opts = MockOpts()
        mock_opts.external_port = external_port
        mock_opts.external_ip = external_ip
        self.opts = mock_opts
        self.alarm_queue = AlarmQueue()
        self.connection_pool = []
        self.network_num = DEFAULT_NETWORK_NUM
        self.idx = 1

        self.broadcast_messages = []
        mock_opts = MockOpts()
        super(MockNode, self).__init__(mock_opts)

        self._tx_service = TransactionService(self, self.network_num)
        self._tx_services = {}

    def broadcast(self, msg, broadcasting_conn=None, prepend_to_queue=False, network_num=None,
                  connection_types=None, exclude_relays=False):
        self.broadcast_messages.append(msg)
        return []

    def get_tx_service(self, _network_num=None):
        return self._tx_service


class MockOpts(object):

    def __init__(self, node_id="foo", external_ip="127.0.0.1", external_port=8000, bloxroute_version="v1.5",
                 log_path="./", to_stdout=True, index=1, sid_start=1, sid_end=100000, sid_expire_time=99999,
                 outbound_peers=None, blockchain_network_num=DEFAULT_NETWORK_NUM, node_type=NodeType.RELAY,
                 dump_removed_short_ids=False):
        if outbound_peers is None:
            outbound_peers = []
        self.node_id = node_id
        self.external_ip = external_ip
        self.external_port = external_port
        self.bloxroute_version = bloxroute_version
        self.log_path = log_path
        self.to_stdout = to_stdout
        self.index = index
        self.sid_start = sid_start
        self.sid_end = sid_end
        self.sid_expire_time = sid_expire_time
        self.outbound_peers = outbound_peers
        self.blockchain_network_num = blockchain_network_num
        self.node_type = node_type
        self.blockchain_networks = [
            BlockchainNetworkModel(protocol="Bitcoin", network="Mainnet", network_num=0, final_tx_confirmations_count=2),
            BlockchainNetworkModel(protocol="Bitcoin", network="Testnet", network_num=1, final_tx_confirmations_count=2),
            BlockchainNetworkModel(protocol="Ethereum", network="Mainnet", network_num=2, final_tx_confirmations_count=2),
            BlockchainNetworkModel(protocol="Ethereum", network="Testnet", network_num=3, final_tx_confirmations_count=2)
        ]
        self.transaction_pool_memory_limit = 200000000
        self.throughput_debugging = False
        self.enable_buffered_send = False
        self.track_detailed_sent_messages = True
        self.dump_detailed_report_at_memory_usage = 100
        self.dump_removed_short_ids = False
        self.dump_missing_short_ids = False
        self.memory_stats_interval = 3600
