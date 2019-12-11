import uuid
from enum import Flag, auto

from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.connections.connection_pool import ConnectionPool
from bxcommon.connections.connection_type import ConnectionType
from bxcommon.constants import LOCALHOST
from bxcommon.test_utils import helpers
from bxcommon.test_utils.mocks.mock_connection import MockConnection
from bxcommon.test_utils.mocks.mock_node import MockNode
from bxcommon.test_utils.mocks.mock_socket_connection import MockSocketConnection


class ConnectionPoolTest(AbstractTestCase):

    def setUp(self):
        self.conn_pool1 = ConnectionPool()

        self.fileno1 = 1
        self.ip1 = "123.123.123.123"
        self.port1 = 1000
        self.node1 = MockNode(helpers.get_common_opts(1001, external_ip="128.128.128.128"))
        self.node_id1 = str(uuid.uuid1())
        self.conn1 = MockConnection(MockSocketConnection(self.fileno1, ip_address=self.ip1, port=self.port1), self.node1)

        self.fileno2 = 5
        self.ip2 = "234.234.234.234"
        self.port2 = 2000
        self.node2 = MockNode(helpers.get_common_opts(1003, external_ip="321.321.321.321"))
        self.node_id2 = str(uuid.uuid1())
        self.conn2 = MockConnection(MockSocketConnection(self.fileno2, ip_address=self.ip2, port=self.port2), self.node2)

        self.fileno3 = 6
        self.ip3 = "234.234.234.234"
        self.port3 = 3000
        self.node3 = MockNode(helpers.get_common_opts(1003, external_ip="213.213.213.213."))
        self.node_id3 = str(uuid.uuid1())
        self.conn3 = MockConnection(MockSocketConnection(self.fileno3, ip_address=self.ip3, port=self.port3), self.node3)

    def test_add(self):
        self.conn_pool1.add(self.fileno1, self.ip1, self.port1, self.conn1)
        self.assertEqual(self.conn1, self.conn_pool1.by_fileno[self.fileno1])
        self.assertEqual(self.conn1, self.conn_pool1.by_ipport[(self.ip1, self.port1)])
        self.assertEqual(1, self.conn_pool1.count_conn_by_ip[self.ip1])

        with self.assertRaises(AssertionError):
            self.conn_pool1.add(self.fileno1, self.ip1, self.port1, self.conn1)

        self.conn_pool1.add(ConnectionPool.INITIAL_FILENO + 1, "0.0.0.0", self.port1, self.conn1)
        self.assertEqual(ConnectionPool.INITIAL_FILENO * 2, self.conn_pool1.len_fileno)

    def test_update(self):
        self.conn_pool1.add(self.fileno1, self.ip1, self.port1, self.conn1)
        self.conn_pool1.add(self.fileno2, self.ip2, self.port2, self.conn2)
        self.conn_pool1.update_port(self.port1, self.port2, self.conn1)
        self.assertEqual(self.conn1, self.conn_pool1.get_by_ipport(self.ip1, self.port2))
        self.assertFalse(self.conn_pool1.has_connection(self.ip1, self.port1))

    def test_update_connnection_type(self):
        self.conn_pool1.add(self.fileno1, self.ip1, self.port1, self.conn1)
        self.conn_pool1.add(self.fileno2, self.ip2, self.port2, self.conn2)

        mock_connections = self.conn_pool1.get_by_connection_type(self.conn1.CONNECTION_TYPE)
        self.assertIn(self.conn1, mock_connections)
        self.assertIn(self.conn2, mock_connections)

        self.conn_pool1.update_connection_type(self.conn1, ConnectionType.RELAY_TRANSACTION)

        mock_connections = self.conn_pool1.get_by_connection_type(self.conn2.CONNECTION_TYPE)
        self.assertNotIn(self.conn1, mock_connections)
        self.assertIn(self.conn2, mock_connections)

        relay_connections = self.conn_pool1.get_by_connection_type(self.conn1.CONNECTION_TYPE)
        self.assertIn(self.conn1, relay_connections)
        self.assertNotIn(self.conn2, relay_connections)

    def test_has_connection(self):
        self._add_connections()
        self.assertTrue(self.conn_pool1.has_connection(self.ip1, self.port1))
        self.assertFalse(self.conn_pool1.has_connection("111.111.111.111", self.port1))
        self.assertFalse(self.conn_pool1.has_connection("111.111.111.111", 1))
        self.assertFalse(self.conn_pool1.has_connection(self.ip1, 1))

    def test_get_byipport(self):
        self._add_connections()
        self.assertEqual(self.conn1, self.conn_pool1.get_by_ipport(self.ip1, self.port1))
        with self.assertRaises(KeyError):
            self.conn_pool1.get_by_ipport(self.ip1, 1)

    def test_get_by_connection_type(self):
        self.conn1.CONNECTION_TYPE = ConnectionType.EXTERNAL_GATEWAY
        self.conn2.CONNECTION_TYPE = ConnectionType.RELAY_BLOCK
        self.conn3.CONNECTION_TYPE = ConnectionType.RELAY_ALL
        self._add_connections()

        gateway_connections = self.conn_pool1.get_by_connection_type(ConnectionType.EXTERNAL_GATEWAY)
        self.assertEqual(1, len(gateway_connections))
        self.assertIn(self.conn1, gateway_connections)

        relay_connections = self.conn_pool1.get_by_connection_type(ConnectionType.RELAY_BLOCK)
        self.assertEqual(2, len(relay_connections))
        self.assertIn(self.conn2, relay_connections)
        self.assertIn(self.conn3, relay_connections)

    def test_get_by_connection_types(self):
        self.conn1.CONNECTION_TYPE = ConnectionType.EXTERNAL_GATEWAY
        self.conn2.CONNECTION_TYPE = ConnectionType.RELAY_BLOCK
        self.conn3.CONNECTION_TYPE = ConnectionType.RELAY_ALL
        self._add_connections()

        gateway_and_relay_block_connections = self.conn_pool1.get_by_connection_types([
            ConnectionType.EXTERNAL_GATEWAY, ConnectionType.RELAY_TRANSACTION
        ])
        self.assertEqual(2, len(gateway_and_relay_block_connections))
        self.assertIn(self.conn1, gateway_and_relay_block_connections)
        self.assertIn(self.conn3, gateway_and_relay_block_connections)

    def test_get_by_fileno(self):
        self._add_connections()
        self.assertEqual(self.conn1, self.conn_pool1.get_by_fileno(self.fileno1))
        self.assertEqual(self.conn2, self.conn_pool1.get_by_fileno(self.fileno2))
        self.conn_pool1.add(6000, "0.0.0.0", 4000, self.conn3)
        self.assertIsNone(self.conn_pool1.get_by_fileno(7000))
        self.assertIsNone(self.conn_pool1.get_by_fileno(2))

    def test_get_num_conn_by_ip(self):
        self._add_connections()
        self.assertEqual(1, self.conn_pool1.get_num_conn_by_ip(self.ip1))
        self.assertEqual(2, self.conn_pool1.get_num_conn_by_ip(self.ip2))
        self.assertEqual(0, self.conn_pool1.get_num_conn_by_ip("222.222.222.222"))

    def test_delete(self):
        self._add_connections()
        self.conn_pool1.delete(self.conn1)
        self.assertIsNone(self.conn_pool1.get_by_fileno(self.fileno1))
        with self.assertRaises(KeyError):
            self.conn_pool1.get_by_ipport(self.ip1, self.port1)

        self.conn_pool1.delete(self.conn2)
        self.assertIsNone(self.conn_pool1.get_by_fileno(self.fileno2))
        self.assertEqual(1, self.conn_pool1.count_conn_by_ip[self.ip2])

    # noinspection PyTypeChecker
    def test_delete_removes_multiple_types(self):
        class TestConnectionType(Flag):
            A = auto()
            B = auto()
            AB = A | B

        conn = MockConnection(MockSocketConnection(ip_address=LOCALHOST, port=8000), self.node1)
        conn.CONNECTION_TYPE = TestConnectionType.AB
        self.conn_pool1.add(self.fileno1, LOCALHOST, 8000, conn)
        self.assertIn(conn, self.conn_pool1.get_by_connection_type(TestConnectionType.A))
        self.assertIn(conn, self.conn_pool1.get_by_connection_type(TestConnectionType.B))

        self.conn_pool1.delete(conn)
        self.assertNotIn(conn, self.conn_pool1.get_by_connection_type(TestConnectionType.A))
        self.assertNotIn(conn, self.conn_pool1.get_by_connection_type(TestConnectionType.B))

    def test_delete_by_fileno(self):
        self._add_connections()
        self.conn_pool1.delete_by_fileno(self.fileno1)
        with self.assertRaises(KeyError):
            self.conn_pool1.get_by_ipport(self.ip1, self.port1)

    def test_iter(self):
        self._add_connections()
        pool_connections = list(iter(self.conn_pool1))
        self.assertEqual(3, len(pool_connections))
        self.assertTrue(self.conn1 in pool_connections)
        self.assertTrue(self.conn2 in pool_connections)
        self.assertTrue(self.conn3 in pool_connections)

    def test_len(self):
        self.assertEqual(0, len(self.conn_pool1))
        self._add_connections()
        self.assertEqual(3, len(self.conn_pool1))
        self.conn_pool1.delete(self.conn2)
        self.assertEqual(2, len(self.conn_pool1))

    def test_get_by_node_id(self):
        self._add_connections()
        self.conn1.peer_id = self.node_id2
        self.conn_pool1.index_conn_node_id(self.node_id2, self.conn1)
        connections_for_node_id = self.conn_pool1.get_by_node_id(self.node_id2)
        self.assertEqual(1, len(connections_for_node_id))
        self.conn_pool1.add(4000, "0.0.0.0", 6000, self.conn2)
        self.conn_pool1.index_conn_node_id(self.node_id2, self.conn2)
        connections_for_node_id = self.conn_pool1.get_by_node_id(self.node_id2)
        self.assertEqual(2, len(connections_for_node_id))
        self.assertEqual(0, len(self.conn_pool1.get_by_node_id("node_id")))

    def _add_connections(self):
        self.conn_pool1.add(self.fileno1, self.ip1, self.port1, self.conn1)
        self.conn_pool1.add(self.fileno2, self.ip2, self.port2, self.conn2)
        self.conn_pool1.add(self.fileno3, self.ip3, self.port3, self.conn3)
