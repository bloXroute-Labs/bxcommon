import unittest
import uuid

from bxcommon.connections.connection_pool import ConnectionPool
from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.test_utils.mocks.mock_connection import MockConnection
from bxcommon.test_utils.mocks.mock_node import MockNode


class ConnectionPoolTest(AbstractTestCase):

    def setUp(self):
        self.conn_pool1 = ConnectionPool()

        self.fileno1 = 1
        self.ip1 = "123.123.123.123"
        self.port1 = 1000
        self.node1 = MockNode("128.128.128.128", 1001)
        self.node_id1 = str(uuid.uuid1())
        self.conn1 = MockConnection(self.fileno1, (self.ip1, self.port1), self.node1)


        self.fileno2 = 5
        self.ip2 = "234.234.234.234"
        self.port2 = 2000
        self.node2 = MockNode("321.321.321.321", 1003)
        self.node_id2 = str(uuid.uuid1())
        self.conn2 = MockConnection(self.fileno2, (self.ip2, self.port2), self.node2)


        self.fileno3 = 6
        self.ip3 = "234.234.234.234"
        self.port3 = 3000
        self.node3 = MockNode("213.213.213.213", 1003)
        self.node_id3 = str(uuid.uuid1())
        self.conn3 = MockConnection(self.fileno3, (self.ip3, self.port3), self.node3)

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

    def test_has_connection(self):
        self.add_conn()
        self.assertTrue(self.conn_pool1.has_connection(self.ip1, self.port1))
        self.assertFalse(self.conn_pool1.has_connection("111.111.111.111", self.port1))
        self.assertFalse(self.conn_pool1.has_connection("111.111.111.111", 1))
        self.assertFalse(self.conn_pool1.has_connection(self.ip1, 1))

    def test_get_byipport(self):
        self.add_conn()
        self.assertEqual(self.conn1, self.conn_pool1.get_by_ipport(self.ip1, self.port1))
        with self.assertRaises(KeyError):
            self.conn_pool1.get_by_ipport(self.ip1, 1)

    def test_get_by_fileno(self):
        self.add_conn()
        self.assertEqual(self.conn1, self.conn_pool1.get_by_fileno(self.fileno1))
        self.assertEqual(self.conn2, self.conn_pool1.get_by_fileno(self.fileno2))
        self.conn_pool1.add(6000, "0.0.0.0", 4000, self.conn3)
        self.assertIsNone(self.conn_pool1.get_by_fileno(7000))
        self.assertIsNone(self.conn_pool1.get_by_fileno(2))

    def test_get_num_conn_by_ip(self):
        self.add_conn()
        self.assertEqual(1, self.conn_pool1.get_num_conn_by_ip(self.ip1))
        self.assertEqual(2, self.conn_pool1.get_num_conn_by_ip(self.ip2))
        self.assertEqual(0, self.conn_pool1.get_num_conn_by_ip("222.222.222.222"))

    def test_delete(self):
        self.add_conn()
        self.conn_pool1.delete(self.conn1)
        self.assertIsNone(self.conn_pool1.get_by_fileno(self.fileno1))
        with self.assertRaises(KeyError):
            self.conn_pool1.get_by_ipport(self.ip1, self.port1)

        self.conn_pool1.delete(self.conn2)
        self.assertIsNone(self.conn_pool1.get_by_fileno(self.fileno2))
        self.assertEqual(1, self.conn_pool1.count_conn_by_ip[self.ip2])

    def test_delete_by_fileno(self):
        self.add_conn()
        self.conn_pool1.delete_by_fileno(self.fileno1)
        with self.assertRaises(KeyError):
            self.conn_pool1.get_by_ipport(self.ip1, self.port1)

    def test_iter(self):
        self.add_conn()
        pool_connections = list(iter(self.conn_pool1))
        self.assertEquals(3, len(pool_connections))
        self.assertTrue(self.conn1 in pool_connections)
        self.assertTrue(self.conn2 in pool_connections)
        self.assertTrue(self.conn3 in pool_connections)

    def test_len(self):
        self.assertEqual(0, len(self.conn_pool1))
        self.add_conn()
        self.assertEqual(3, len(self.conn_pool1))
        self.conn_pool1.delete(self.conn2)
        self.assertEqual(2, len(self.conn_pool1))

    def add_conn(self):
        self.conn_pool1.add(self.fileno1, self.ip1, self.port1, self.conn1)
        self.conn_pool1.add(self.fileno2, self.ip2, self.port2, self.conn2)
        self.conn_pool1.add(self.fileno3, self.ip3, self.port3, self.conn3)
