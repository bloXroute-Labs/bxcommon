from argparse import Namespace
from typing import List

from bxcommon.connections.abstract_connection import AbstractConnection
from bxcommon.connections.abstract_node import AbstractNode
from bxcommon.connections.node_type import NodeType
from bxcommon.constants import DEFAULT_NETWORK_NUM
from bxcommon.services.transaction_service import TransactionService
from bxcommon.utils.alarm_queue import AlarmQueue


class MockNode(AbstractNode):
    NODE_TYPE = NodeType.RELAY

    def __init__(self, opts: Namespace):
        super(MockNode, self).__init__(opts)
        self.alarm_queue = AlarmQueue()
        self.network_num = DEFAULT_NETWORK_NUM

        self.broadcast_messages = []

        self._tx_service = TransactionService(self, self.network_num)
        self._tx_services = {}

    def broadcast(self, msg, broadcasting_conn=None, prepend_to_queue=False, connection_types=None) -> List[AbstractConnection]:
        self.broadcast_messages.append(msg)
        return []

    def get_tx_service(self, _network_num=None):
        return self._tx_service
