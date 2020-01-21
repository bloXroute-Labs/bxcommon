import time
from typing import Optional, List
from mock import patch, MagicMock

from bxcommon.models.node_type import NodeType
from bxcommon.test_utils.helpers import async_test
from bxcommon.test_utils.mocks.mock_node_ssl_service import MockNodeSSLService
from bxcommon.network.ip_endpoint import IpEndpoint
from bxcommon.network.peer_info import ConnectionPeerInfo
from bxcommon.connections.abstract_connection import AbstractConnection
from bxcommon.services.broadcast_service import BroadcastService
from bxcommon import constants
from bxcommon.connections.abstract_node import AbstractNode
from bxcommon.connections.connection_state import ConnectionState
from bxcommon.connections.connection_type import ConnectionType
from bxcommon.constants import MAX_CONNECT_RETRIES
from bxcommon.models.outbound_peer_model import OutboundPeerModel
from bxcommon.network.socket_connection_state import SocketConnectionState
from bxcommon.services import sdn_http_service
from bxcommon.test_utils import helpers
from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.test_utils.mocks.mock_connection import MockConnection
from bxcommon.utils import memory_utils

from bxutils.services.node_ssl_service import NodeSSLService


class TestNode(AbstractNode):
    NODE_TYPE = NodeType.GATEWAY

    def __init__(self, opts, node_ssl_service: Optional[NodeSSLService] = None):
        if node_ssl_service is None:
            node_ssl_service = MockNodeSSLService(NodeType.EXTERNAL_GATEWAY, MagicMock())
        super(TestNode, self).__init__(opts, node_ssl_service)

    def get_outbound_peer_info(self) -> List[ConnectionPeerInfo]:
        return [MagicMock()]

    def send_request_for_peers(self):
        pass

    def build_connection(self, socket_connection):
        return MockConnection(socket_connection, self)

    def on_failed_connection_retry(self, ip: str, port: int, connection_type: ConnectionType) -> None:
        sdn_http_service.submit_peer_connection_error_event(self.opts.node_id, ip, port)

    def get_tx_service(self, network_num=None):
        pass

    def get_broadcast_service(self) -> BroadcastService:
        pass

    def send_request_for_relay_peers(self):
        pass

    def _sync_tx_services(self):
        self.start_sync_time = time.time()

    def _transaction_sync_timeout(self):
        pass

    def _check_sync_relay_connections(self):
        pass

    def _authenticate_connection(self, connection: Optional[AbstractConnection]) -> None:
        pass


class AbstractNodeTest(AbstractTestCase):
    def setUp(self):
        sdn_http_service.submit_peer_connection_error_event = MagicMock()

        self.node = TestNode(helpers.get_common_opts(4321), None)
        self.fileno = 1
        self.ip = "123.123.123.123"
        self.port = 8000
        self.connection = helpers.create_connection(MockConnection, self.node, file_no=self.fileno, ip=self.ip,
                                                    port=self.port, add_to_pool=False, from_me=True)
        self.connection.dispose = MagicMock(side_effect=self.connection.dispose)
        self.socket_connection = self.connection.socket_connection

    def test_connection_exists(self):
        self.assertFalse(self.node.connection_exists(self.ip, self.port))
        self.node.connection_pool.add(self.fileno, self.ip, self.port, self.connection)
        self.assertTrue(self.node.connection_exists(self.ip, self.port))

    def test_on_connection_added_new_connection(self):
        self.node.on_connection_added(self.socket_connection)
        self.assertTrue(self.node.connection_exists(self.ip, self.port))
        self._assert_socket_connected()

    def test_on_connection_added_duplicate(self):
        self.node.connection_exists = MagicMock(return_value=True)
        self.node.on_connection_added(self.socket_connection)

        self.assertIsNone(self.node.connection_pool.get_by_fileno(self.fileno))
        self._assert_socket_disconnected(False)

    def test_on_connection_added_unknown_connection_type(self):
        self.node.build_connection = MagicMock(return_value=None)
        self.node.on_connection_added(self.socket_connection)

        self.assertIsNone(self.node.connection_pool.get_by_fileno(self.fileno))
        self._assert_socket_disconnected(False)

    def test_on_connection_closed(self):
        self.node.connection_pool.add(self.fileno, self.ip, self.port, self.connection)
        self.node.alarm_queue.register_alarm = MagicMock()
        self.connection.mark_for_close()
        self.node.on_connection_closed(self.fileno)
        self.connection.dispose.assert_called_once()

        self.assertFalse(self.node.connection_exists(self.ip, self.port))
        self.node.alarm_queue.register_alarm.assert_any_call(1, self.node._retry_init_client_socket, self.ip,
                                                             self.port, self.connection.CONNECTION_TYPE)

    def test_on_updated_peers(self):
        self.node.connection_pool.add(self.fileno, self.ip, self.port, self.connection)
        self.node.opts.outbound_peers = [OutboundPeerModel("222.222.222.222", 2000, node_type=NodeType.GATEWAY)]
        self.node.outbound_peers = [OutboundPeerModel("111.111.111.111", 1000, node_type=NodeType.GATEWAY),
                                    OutboundPeerModel("222.222.222.222", 2000, node_type=NodeType.GATEWAY),
                                    OutboundPeerModel(self.ip, self.port, node_type=NodeType.GATEWAY)]

        outbound_peer_models = [OutboundPeerModel("111.111.111.111", 1000, node_type=NodeType.GATEWAY)]
        self.node.on_updated_peers(outbound_peer_models)

        self.assertEqual(outbound_peer_models, self.node.outbound_peers)
        self._assert_socket_disconnected(False)

    def test_on_bytes_received(self):
        data = helpers.generate_bytearray(250)
        self.node.connection_pool.add(self.fileno, self.ip, self.port, self.connection)
        self.node.on_bytes_received(self.fileno, data)
        self.assertEqual(data, self.connection.inputbuf.input_list[0])

    def test_get_bytes_to_send(self):
        data = helpers.generate_bytearray(250)
        self.connection.outputbuf.output_msgs.append(data)
        self.node.connection_pool.add(self.fileno, self.ip, self.port, self.connection)
        self.assertEqual(data, self.node.get_bytes_to_send(self.fileno))

    def test_on_bytes_sent(self):
        self.connection.outputbuf.output_msgs.append(helpers.generate_bytearray(200))
        self.connection.outputbuf.output_msgs.append(helpers.generate_bytearray(200))
        self.node.connection_pool.add(self.fileno, self.ip, self.port, self.connection)
        advance_by = 8
        self.node.on_bytes_sent(self.fileno, advance_by)
        self.assertEqual(advance_by, self.connection.outputbuf.index)

    @async_test
    async def test_close(self):
        self.node.connection_pool.add(self.fileno, self.ip, self.port, self.connection)
        self.assertIn(self.connection, self.node.connection_pool.by_fileno)
        await self.node.close()
        self.assertNotIn(self.connection, self.node.connection_pool.by_fileno)
        self.connection.dispose.assert_called_once()

    def test_enqueue_connection(self):

        self.assertNotIn(
            ConnectionPeerInfo(IpEndpoint(self.ip, self.port), ConnectionType.RELAY_BLOCK),
            self.node.pending_connection_requests
        )
        self.node.enqueue_connection(self.ip, self.port, ConnectionType.GATEWAY)
        self.assertIn(
            ConnectionPeerInfo(IpEndpoint(self.ip, self.port), ConnectionType.GATEWAY),
            self.node.pending_connection_requests
        )

    def test_dequeue_connection_requests(self):
        self.assertIsNone(self.node.dequeue_connection_requests())
        self.node.pending_connection_requests.add(
            ConnectionPeerInfo(IpEndpoint(self.ip, self.port), ConnectionType.RELAY_BLOCK)
        )
        self.node.pending_connection_requests.add(
            ConnectionPeerInfo(IpEndpoint(self.ip, self.port), ConnectionType.RELAY_TRANSACTION)
        )
        pending_connection_requests = self.node.dequeue_connection_requests()
        self.assertEqual(1, len(pending_connection_requests))
        peer_info = next(iter(pending_connection_requests))
        self.assertEqual(IpEndpoint(self.ip, self.port), peer_info.endpoint)
        self.assertEqual(ConnectionType.RELAY_BLOCK, peer_info.connection_type)
        self.assertIsNone(self.node.dequeue_connection_requests())

    def test_connection_timeout_established(self):
        self.connection.state = ConnectionState.ESTABLISHED
        self.assertEqual(0, self.node._connection_timeout(self.connection))
        self._assert_socket_connected()

    def test_connection_timeout_closed(self):
        self.connection.mark_for_close()
        self.assertEqual(0, self.node._connection_timeout(self.connection))

    def test_connection_timeout_connecting(self):
        self.connection.state = ConnectionState.CONNECTING
        self.assertEqual(0, self.node._connection_timeout(self.connection))
        self._assert_socket_disconnected(True)

    def test_get_next_retry_timeout(self):
        self.connection.CONNECTION_TYPE = ConnectionType.BLOCKCHAIN_NODE
        self.node.connection_pool.add(self.fileno, self.ip, self.port, self.connection)

        self.assertEqual(1, self.node._get_next_retry_timeout(self.ip, self.port))

        self.node.num_retries_by_ip[(self.ip, self.port)] += 1
        self.assertEqual(1, self.node._get_next_retry_timeout(self.ip, self.port))

        self.node.num_retries_by_ip[(self.ip, self.port)] += 1
        self.assertEqual(2, self.node._get_next_retry_timeout(self.ip, self.port))

        self.node.num_retries_by_ip[(self.ip, self.port)] += 1
        self.assertEqual(3, self.node._get_next_retry_timeout(self.ip, self.port))

        self.node.num_retries_by_ip[(self.ip, self.port)] += 1
        self.assertEqual(5, self.node._get_next_retry_timeout(self.ip, self.port))

        self.node.num_retries_by_ip[(self.ip, self.port)] += 1
        self.assertEqual(8, self.node._get_next_retry_timeout(self.ip, self.port))

        self.node.num_retries_by_ip[(self.ip, self.port)] += 1
        self.assertEqual(13, self.node._get_next_retry_timeout(self.ip, self.port))

        # caps at 13
        self.node.num_retries_by_ip[(self.ip, self.port)] += 1
        self.assertEqual(13, self.node._get_next_retry_timeout(self.ip, self.port))

        self.node.num_retries_by_ip[(self.ip, self.port)] += 10
        self.assertEqual(13, self.node._get_next_retry_timeout(self.ip, self.port))

    def test_retry_init_client_socket(self):
        self.node._retry_init_client_socket(self.ip, self.port, ConnectionType.RELAY_ALL)
        self.assertIn(
            ConnectionPeerInfo(IpEndpoint(self.ip, self.port), ConnectionType.RELAY_ALL),
            self.node.pending_connection_requests
        )
        self.assertEqual(1, self.node.num_retries_by_ip[(self.ip, self.port)])

        self.node._retry_init_client_socket(self.ip, self.port, ConnectionType.RELAY_ALL)
        self.assertEqual(2, self.node.num_retries_by_ip[(self.ip, self.port)])

    def test_destroy_conn_no_retry(self):
        self.node.alarm_queue.register_alarm = MagicMock()
        self.connection.mark_for_close(False)
        self.node._destroy_conn(self.connection)

        self.assertFalse(self.node.connection_exists(self.ip, self.port))
        self.node.alarm_queue.register_alarm.assert_not_called()
        sdn_http_service.submit_peer_connection_error_event.assert_called_with(
            self.node.opts.node_id, self.ip, self.port
        )

    def test_destroy_conn_retry(self):
        self.node.alarm_queue.register_alarm = MagicMock()
        self.connection.mark_for_close()

        self.node._destroy_conn(self.connection)
        self.assertFalse(self.node.connection_exists(self.ip, self.port))
        self.node.alarm_queue.register_alarm.assert_called_once()
        sdn_http_service.submit_peer_connection_error_event.assert_not_called()

    def test_destroy_conn_max_retries(self):
        self.node.alarm_queue.register_alarm = MagicMock()
        self.node.num_retries_by_ip[(self.ip, self.port)] = MAX_CONNECT_RETRIES
        self.connection.mark_for_close()

        self.node._destroy_conn(self.connection)
        self.assertFalse(self.node.connection_exists(self.ip, self.port))
        self.node.alarm_queue.register_alarm.assert_not_called()
        sdn_http_service.submit_peer_connection_error_event.assert_called_with(
            self.node.opts.node_id, self.ip, self.port
        )

    @patch("bxcommon.connections.abstract_node.memory_logger")
    def test_dump_memory_usage(self, logger_mock):
        # set to dump memory at 10 MB
        self.node.next_report_mem_usage_bytes = 10 * 1024 * 1024

        # current memory usage is 5 MB
        memory_utils.get_app_memory_usage = MagicMock(return_value=5 * 1024 * 1024)

        self.node.dump_memory_usage()
        # expect that memory details are not logged
        self.assertEqual(10 * 1024 * 1024, self.node.next_report_mem_usage_bytes)
        logger_mock.assert_not_called()

        # current memory usage goes up to 11 MB
        memory_utils.get_app_memory_usage = MagicMock(return_value=11 * 1024 * 1024)

        self.node.dump_memory_usage()
        # expect that memory details are logged
        self.assertEqual(11 * 1024 * 1024 + constants.MEMORY_USAGE_INCREASE_FOR_NEXT_REPORT_BYTES,
                         self.node.next_report_mem_usage_bytes)
        logger_mock.statistics.assert_called_once()

        # current memory usage goes up to 15 MB
        memory_utils.get_app_memory_usage = MagicMock(return_value=15 * 1024 * 1024)

        self.node.dump_memory_usage()
        # expect that memory details are not logged again
        self.assertEqual(11 * 1024 * 1024 + constants.MEMORY_USAGE_INCREASE_FOR_NEXT_REPORT_BYTES,
                         self.node.next_report_mem_usage_bytes)
        logger_mock.statistics.assert_called_once()

    def _assert_socket_connected(self):
        self.assertFalse(self.socket_connection.state & SocketConnectionState.MARK_FOR_CLOSE)

    def _assert_socket_disconnected(self, should_retry: bool):
        self.assertTrue(self.socket_connection.state & SocketConnectionState.MARK_FOR_CLOSE)
        if should_retry:
            self.assertFalse(self.socket_connection.state & SocketConnectionState.DO_NOT_RETRY)
        else:
            self.assertTrue(self.socket_connection.state & SocketConnectionState.DO_NOT_RETRY)
