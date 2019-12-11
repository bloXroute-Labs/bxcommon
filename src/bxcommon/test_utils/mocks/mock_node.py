from argparse import Namespace
from typing import List, Optional
from mock import MagicMock

from bxcommon.connections.abstract_connection import AbstractConnection
from bxcommon.connections.abstract_node import AbstractNode
from bxcommon.connections.connection_type import ConnectionType
from bxcommon.constants import DEFAULT_NETWORK_NUM
from bxcommon.models.node_type import NodeType
from bxcommon.network.socket_connection_protocol import SocketConnectionProtocol
from bxcommon.services.broadcast_service import BroadcastService
from bxcommon.services.transaction_service import TransactionService
from bxcommon.test_utils.mocks.mock_node_ssl_service import MockNodeSSLService
from bxcommon.utils.alarm_queue import AlarmQueue

from bxutils.services.node_ssl_service import NodeSSLService


class MockNode(AbstractNode):

    NODE_TYPE = NodeType.RELAY

    def __init__(self, opts: Namespace, node_ssl_service: Optional[NodeSSLService] = None):
        if node_ssl_service is None:
            node_ssl_service = MockNodeSSLService(self.NODE_TYPE, MagicMock())
        super(MockNode, self).__init__(opts, node_ssl_service)
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

    def get_outbound_peer_addresses(self):
        pass

    def get_broadcast_service(self) -> BroadcastService:
        pass

    def send_request_for_relay_peers(self):
        pass

    def build_connection(self, socket_connection: SocketConnectionProtocol) -> Optional[AbstractConnection]:
        pass

    def on_failed_connection_retry(self, ip: str, port: int, connection_type: ConnectionType) -> None:
        pass

    def _sync_tx_services(self):
        pass

    def _transaction_sync_timeout(self):
        pass

    def _check_sync_relay_connections(self):
        pass

    def _authenticate_connection(self, connection: Optional[AbstractConnection]) -> None:
        pass
