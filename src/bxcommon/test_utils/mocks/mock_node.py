from bxcommon.connections.connection_type import ConnectionType
from bxcommon.connections.node_type import NodeType
from bxcommon.constants import DEFAULT_NETWORK_NUM
from bxcommon.services.transaction_service import TransactionService
from bxcommon.utils.alarm import AlarmQueue
from bxcommon.connections.abstract_node import AbstractNode


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

        self._tx_service = TransactionService(self)

    def broadcast(self, msg, requester=None, prepend_to_queue=False, network_num=None,
                  connection_type=ConnectionType.RELAY):
        self.broadcast_messages.append(msg)
        return []

    def get_tx_service(self, _network_num=None):
        return self._tx_service


class MockOpts(object):

    def __init__(self, node_id="foo", external_ip="127.0.0.1", external_port=8000, bloxroute_version="v1.5",
                 log_path="./", to_stdout=True, index=1, sid_start=1, sid_end=100000, sid_expire_time=99999,
                 outbound_peers=None, network_num=DEFAULT_NETWORK_NUM):
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
        self.network_num = network_num
