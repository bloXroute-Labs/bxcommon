import functools
from asyncio import Future
from typing import List, Optional

from mock import MagicMock

from bxcommon import constants
from bxcommon.connections.abstract_connection import AbstractConnection
from bxcommon.connections.abstract_node import AbstractNode
from bxcommon.connections.connection_state import ConnectionState
from bxcommon.connections.connection_type import ConnectionType
from bxcommon.constants import DEFAULT_NETWORK_NUM
from bxcommon.models.node_type import NodeType
from bxcommon.network.abstract_socket_connection_protocol import AbstractSocketConnectionProtocol
from bxcommon.network.peer_info import ConnectionPeerInfo
from bxcommon.services.broadcast_service import BroadcastService
from bxcommon.services.transaction_service import TransactionService
from bxcommon.test_utils.mocks.mock_node_ssl_service import MockNodeSSLService
from bxcommon.utils.alarm_queue import AlarmQueue
from bxcommon.common_opts import CommonOpts
from bxcommon.utils.stats.memory_statistics_service import memory_statistics
from bxutils.services.node_ssl_service import NodeSSLService


class MockNode(AbstractNode):
    NODE_TYPE = NodeType.RELAY

    def __init__(self, opts: CommonOpts, node_ssl_service: Optional[NodeSSLService] = None) -> None:
        if node_ssl_service is None:
            node_ssl_service = MockNodeSSLService(self.NODE_TYPE, MagicMock())
        super(MockNode, self).__init__(opts, node_ssl_service)
        self.alarm_queue = AlarmQueue()
        self.network_num = DEFAULT_NETWORK_NUM

        self.broadcast_messages = []

        self._tx_service = TransactionService(self, self.network_num)
        self._tx_services = {}

    def broadcast(
        self, msg, broadcasting_conn=None, prepend_to_queue=False, connection_types=None
    ) -> List[AbstractConnection]:
        self.broadcast_messages.append(msg)
        return []

    def get_tx_service(self, network_num: Optional[int] = None) -> TransactionService:
        return self._tx_service

    def get_outbound_peer_addresses(self):
        pass

    def get_outbound_peer_info(self) -> List[ConnectionPeerInfo]:
        pass

    def get_broadcast_service(self) -> BroadcastService:
        pass

    def sync_and_send_request_for_relay_peers(self, network_num: int):
        pass

    def build_connection(self, socket_connection: AbstractSocketConnectionProtocol) -> Optional[AbstractConnection]:
        pass

    def process_potential_relays_from_sdn(self, get_potential_relays_future: Future):
        pass

    def on_failed_connection_retry(
        self, ip: str, port: int, connection_type: ConnectionType, connection_state: ConnectionState
    ) -> None:
        pass

    def sync_tx_services(self):
        pass

    def _transaction_sync_timeout(self) -> int:
        pass

    def check_sync_relay_connections(self, conn: AbstractConnection) -> int:
        pass

    def broadcast_transaction(
        self,
        message,
        broadcasting_connection,
        tx_status,
        prepend_to_queue: bool = False
    ) -> None:
        pass

    def on_new_subscriber_request(self) -> None:
        pass

    def init_memory_stats_logging(self):
        memory_statistics.set_node(self)
        memory_statistics.start_recording(
            functools.partial(
                self.record_mem_stats,
                constants.GC_LOW_MEMORY_THRESHOLD,
                constants.GC_MEDIUM_MEMORY_THRESHOLD,
                constants.GC_HIGH_MEMORY_THRESHOLD
            )
        )

    def reevaluate_transaction_streamer_connection(self) -> None:
        pass
