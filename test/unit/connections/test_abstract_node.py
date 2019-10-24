from mock import patch, MagicMock

from bxcommon import constants
from bxcommon.connections.abstract_node import AbstractNode, DisconnectRequest
from bxcommon.connections.connection_state import ConnectionState
from bxcommon.connections.connection_type import ConnectionType
from bxcommon.constants import DEFAULT_SLEEP_TIMEOUT, MAX_CONNECT_RETRIES
from bxcommon.models.outbound_peer_model import OutboundPeerModel
from bxcommon.services import sdn_http_service
from bxcommon.test_utils import helpers
from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.test_utils.mocks.mock_connection import MockConnection
from bxcommon.utils import memory_utils


class TestNode(AbstractNode):
    def __init__(self, opts):
        super(TestNode, self).__init__(opts)

    def get_outbound_peer_addresses(self):
        return True

    def send_request_for_peers(self):
        pass

    def build_connection(self, socket_connection, ip, port, from_me=False):
        return MockConnection(socket_connection, (ip, port), self, from_me)

    def on_failed_connection_retry(self, ip: str, port: int, connection_type: ConnectionType) -> None:
        sdn_http_service.submit_peer_connection_error_event(self.opts.node_id, ip, port)


class AbstractNodeTest(AbstractTestCase):
    def setUp(self):
        self.node = TestNode(helpers.get_common_opts(4321))
        self.fileno = 1
        self.ip = "123.123.123.123"
        self.port = 8000
        self.connection = helpers.create_connection(MockConnection, self.node, fileno=self.fileno, ip=self.ip,
                                                    port=self.port, add_to_pool=False)
        self.connection.close = MagicMock(side_effect=self.connection.close)
        self.socket_connection = self.connection.socket_connection

    def test_connection_exists(self):
        self.assertFalse(self.node.connection_exists(self.ip, self.port))
        self.node.connection_pool.add(self.fileno, self.ip, self.port, self.connection)
        self.assertTrue(self.node.connection_exists(self.ip, self.port))

    def test_on_connection_added_new_connection(self):
        self.node.on_connection_added(self.socket_connection, self.ip, self.port, True)
        self.assertTrue(self.node.connection_exists(self.ip, self.port))
        self.assertEqual(0, len(self.node.disconnect_queue))

    def test_on_connection_added_duplicate(self):
        self.node.connection_exists = MagicMock(return_value=True)
        self.node.on_connection_added(self.socket_connection, self.ip, self.port, True)

        self.assertIsNone(self.node.connection_pool.get_by_fileno(self.fileno))
        self.assertEqual(1, len(self.node.disconnect_queue))
        self.assertEqual((self.fileno, False), self.node.disconnect_queue[0])

    def test_on_connection_added_unknown_connection_type(self):
        self.node.build_connection = MagicMock(return_value=None)
        self.node.on_connection_added(self.socket_connection, self.ip, self.port, True)

        self.assertIsNone(self.node.connection_pool.get_by_fileno(self.fileno))
        self.assertEqual(1, len(self.node.disconnect_queue))
        self.assertEqual((self.fileno, True), self.node.disconnect_queue[0])

    def test_on_connection_initialized(self):
        self.node.connection_pool.add(self.fileno, self.ip, self.port, self.connection)
        self.assertEqual(ConnectionState.CONNECTING, self.connection.state)
        self.node.on_connection_initialized(self.fileno)
        self.assertEqual(ConnectionState.INITIALIZED, self.connection.state)

    def test_on_connection_closed(self):
        self.node.connection_pool.add(self.fileno, self.ip, self.port, self.connection)
        with self.assertRaises(ValueError):
            self.node.on_connection_closed(self.fileno, True)

        self.node.alarm_queue.register_alarm = MagicMock()
        self.connection.mark_for_close()
        self.node.on_connection_closed(self.fileno, True)
        self.connection.close.assert_called_once()

        self.assertFalse(self.node.connection_exists(self.ip, self.port))
        self.node.alarm_queue.register_alarm.assert_called_once_with(1, self.node._retry_init_client_socket, self.ip,
                                                                     self.port, self.connection.CONNECTION_TYPE)

    def test_on_updated_peers(self):
        self.node.connection_pool.add(self.fileno, self.ip, self.port, self.connection)
        self.node.opts.outbound_peers = [OutboundPeerModel("222.222.222.222", 2000)]
        self.node.outbound_peers = [OutboundPeerModel("111.111.111.111", 1000),
                                    OutboundPeerModel("222.222.222.222", 2000),
                                    OutboundPeerModel(self.ip, self.port)]

        outbound_peer_models = [OutboundPeerModel("111.111.111.111", 1000)]
        self.node.on_updated_peers(outbound_peer_models)

        self.assertEqual(outbound_peer_models, self.node.outbound_peers)
        self.assertIn((self.fileno, False), self.node.disconnect_queue)

    def test_on_bytes_received(self):
        data = helpers.generate_bytearray(250)
        self.node.connection_pool.add(self.fileno, self.ip, self.port, self.connection)
        self.node.on_bytes_received(self.fileno, data)
        self.assertEqual(data, self.connection.inputbuf.input_list[0])

    def test_on_finished_receiving(self):
        self.connection.process_message = MagicMock()

        some_other_fileno = 2
        self.node.on_finished_receiving(some_other_fileno)
        self.connection.process_message.assert_not_called()

        self.node.connection_pool.add(self.fileno, self.ip, self.port, self.connection)
        self.connection.state = ConnectionState.INITIALIZED

        self.node.on_finished_receiving(self.fileno)
        self.connection.process_message.assert_called_once()
        self.assertEqual(0, len(self.node.disconnect_queue))
        self.connection.process_message.reset_mock()

        self.connection.process_message.side_effect = lambda: self.connection.mark_for_close()
        self.node.on_finished_receiving(self.fileno)
        self.connection.process_message.assert_called_once()
        self.assertIn((self.fileno, False), self.node.disconnect_queue)

    def test_on_finished_receiving_from_me(self):
        self.connection.process_message = MagicMock()

        self.connection.from_me = True
        self.node.connection_pool.add(self.fileno, self.ip, self.port, self.connection)
        self.connection.state = ConnectionState.INITIALIZED

        self.connection.process_message.side_effect = lambda: self.connection.mark_for_close()
        self.node.on_finished_receiving(self.fileno)
        self.connection.process_message.assert_called_once()
        self.assertIn((self.fileno, True), self.node.disconnect_queue)

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

    @patch("bxcommon.connections.abstract_node.AlarmQueue.time_to_next_alarm", return_value=(10, -1))
    @patch("bxcommon.connections.abstract_node.AlarmQueue.fire_ready_alarms", return_value=40)
    def test_get_sleep_timeout(self, mocked_time_to_next_alarm, mocked_fire_ready_alarms):
        self.assertEqual(DEFAULT_SLEEP_TIMEOUT,
                         self.node.get_sleep_timeout(triggered_by_timeout=10, first_call=True))
        self.assertEqual(40, self.node.get_sleep_timeout(triggered_by_timeout=10))
        self.node.connection_queue.append(self.connection)
        self.assertEqual(DEFAULT_SLEEP_TIMEOUT, self.node.get_sleep_timeout(triggered_by_timeout=10))
        mocked_fire_ready_alarms.assert_called()

    def test_close(self):
        self.node.connection_pool.add(self.fileno, self.ip, self.port, self.connection)
        self.assertIn(self.connection, self.node.connection_pool.by_fileno)
        self.node.close()
        self.assertNotIn(self.connection, self.node.connection_pool.by_fileno)
        self.connection.close.assert_called_once()

    def test_enqueue_connection(self):
        self.assertNotIn((self.ip, self.port), self.node.connection_queue)
        self.node.enqueue_connection(self.ip, self.port)
        self.assertIn((self.ip, self.port), self.node.connection_queue)

    def test_enqueue_disconnect(self):
        self.assertNotIn((self.fileno, False), self.node.disconnect_queue)
        self.node.enqueue_disconnect(self.fileno, False)
        self.assertIn((self.fileno, False), self.node.disconnect_queue)

    def test_enqueue_disconnect_unknown_connection(self):
        self.node.enqueue_disconnect(self.fileno)
        self.assertIn((self.fileno, False), self.node.disconnect_queue)
        self.node.on_connection_closed(self.fileno, False)
        self.assertNotIn(self.connection, self.node.connection_pool.by_fileno)

    def test_pop_next_connection_address(self):
        self.assertIsNone(self.node.pop_next_connection_address())
        self.node.connection_queue.append((self.ip, self.port))
        self.assertEqual((self.ip, self.port), self.node.pop_next_connection_address())
        self.assertIsNone(self.node.pop_next_connection_address())

    def test_pop_next_disconnect_connection(self):
        self.assertIsNone(self.node.pop_next_disconnect_connection())
        self.node.disconnect_queue.append(DisconnectRequest(self.fileno, False))
        self.assertEqual((self.fileno, False), self.node.pop_next_disconnect_connection())
        self.assertIsNone(self.node.pop_next_disconnect_connection())

    def test_connection_timeout_established(self):
        self.connection.state = ConnectionState.ESTABLISHED
        self.assertEqual(0, self.node._connection_timeout(self.connection))
        self.assertEqual(0, len(self.node.disconnect_queue))

    def test_connection_timeout_closed(self):
        self.connection.state = ConnectionState.MARK_FOR_CLOSE
        self.assertEqual(0, self.node._connection_timeout(self.connection))
        self.assertEqual(0, len(self.node.disconnect_queue))

    def test_connection_timeout_connecting(self):
        self.connection.state = ConnectionState.CONNECTING
        self.assertEqual(0, self.node._connection_timeout(self.connection))
        self.assertIn((self.fileno, False), self.node.disconnect_queue)

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
        self.assertIn((self.ip, self.port), self.node.connection_queue)
        self.assertEqual(1, self.node.num_retries_by_ip[(self.ip, self.port)])

        self.node._retry_init_client_socket(self.ip, self.port, ConnectionType.RELAY_ALL)
        self.assertEqual(2, self.node.num_retries_by_ip[(self.ip, self.port)])

    def test_retry_init_client_socket_maxed_out(self):
        sdn_http_service.submit_peer_connection_error_event = MagicMock()

        self.node.num_retries_by_ip[(self.ip, self.port)] = MAX_CONNECT_RETRIES
        self.node._retry_init_client_socket(self.ip, self.port, ConnectionType.RELAY_ALL)
        self.assertEqual(0, self.node.num_retries_by_ip[(self.ip, self.port)])

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
