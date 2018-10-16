import unittest
from bxcommon.connections.connection_pool import ConnectionPool
from collections import defaultdict
from bxcommon.test_utils.mocks.mock_connection import MockConnection
from bxcommon.test_utils.mocks.mock_node import MockNode


class ConnectionPoolTest(unittest.TestCase):

    def setUp(self):
        self.conn_pool1 = ConnectionPool()

        self.fileno1 = 1
        self.ip1 = '123.123.123.123'
        self.port1 = 1000
        self.node1 = MockNode('128.128.128.128', 1001)
        self.conn1 = MockConnection(self.fileno1, (self.ip1, self.port1), self.node1)

        self.fileno2 = 5
        self.ip2 = '234.234.234.234'
        self.port2 = 2000
        self.node2 = MockNode('321.321.321.321', 1003)
        self.conn2 = MockConnection(self.fileno2, (self.ip2, self.port2), self.node2)

        self.fileno3 = 6
        self.ip3 = '234.234.234.234'
        self.port3 = 3000
        self.node3 = MockNode('213.213.213.213', 1003)
        self.conn3 = MockConnection(self.fileno3, (self.ip3, self.port3), self.node3)

    def test_add(self):

        self.conn_pool1.add(self.fileno1, self.ip1,self. port1, self.conn1)
        self.assertEqual(self.conn1, self.conn_pool1.byfileno[self.fileno1])
        self.assertEqual(self.conn1, self.conn_pool1.byipport[(self.ip1, self.port1)])
        self.assertEqual(1, self.conn_pool1.count_conn_by_ip[self.ip1])

        with self.assertRaises(AssertionError):
            self.conn_pool1.add(self.fileno1, self.ip1, self.port1, self.conn1)

        self.conn_pool1.add(ConnectionPool.INITIAL_FILENO + 1, '0.0.0.0', self.port1, self.conn1)
        self.assertEqual(ConnectionPool.INITIAL_FILENO * 2, self.conn_pool1.len_fileno)

    def test_has_connection(self):
        self.add_conn()
        self.assertTrue(self.conn_pool1.has_connection(self.ip1, self.port1))
        self.assertFalse(self.conn_pool1.has_connection("111.111.111.111", self.port1))
        self.assertFalse(self.conn_pool1.has_connection("111.111.111.111", 1))
        self.assertFalse(self.conn_pool1.has_connection(self.ip1, 1))

    def test_get_byipport(self):
        self.add_conn()
        self.assertEqual(self.conn1, self.conn_pool1.get_byipport(self.ip1, self.port1))
        with self.assertRaises(KeyError):
            self.conn_pool1.get_byipport(self.ip1, 1)

    def test_get_by_fileno(self):
        self.add_conn()
        self.assertEqual(self.conn1, self.conn_pool1.get_byfileno(self.fileno1))
        self.assertEqual(self.conn2, self.conn_pool1.get_byfileno(self.fileno2))
        self.conn_pool1.add(6000, "0.0.0.0", 4000, self.conn3)
        self.assertIsNone(self.conn_pool1.get_byfileno(7000))
        self.assertIsNone(self.conn_pool1.get_byfileno(2))
        with self.assertRaises(TypeError):
            self.conn_pool1.get_byfileno("g")

    def test_get_num_conn_by_ip(self):
        self.add_conn()
        self.assertEqual(1, self.conn_pool1.get_num_conn_by_ip(self.ip1))
        self.assertEqual(2, self.conn_pool1.get_num_conn_by_ip(self.ip2))
        self.assertEqual(0, self.conn_pool1.get_num_conn_by_ip("222.222.222.222"))

    def test_delete(self):
        self.add_conn()
        self.conn_pool1.delete(self.conn1)
        self.assertIsNone(self.conn_pool1.get_byfileno(self.fileno1))
        with self.assertRaises(KeyError):
            self.conn_pool1.get_byipport(self.ip1, self.port1)

        self.conn_pool1.delete(self.conn2)
        self.assertIsNone(self.conn_pool1.get_byfileno(self.fileno2))
        self.assertEqual(1, self.conn_pool1.count_conn_by_ip[self.ip2])

    def test_delete_byfileno(self):
        self.add_conn()
        self.conn_pool1.delete_byfileno(self.fileno1)
        with self.assertRaises(KeyError):
            self.conn_pool1.get_byipport(self.ip1, self.port1)

    def test_iter(self):
        self.add_conn()
        pool_iter = iter(self.conn_pool1)
        self.assertEqual(self.conn1, pool_iter.next())
        self.assertEqual(self.conn2, pool_iter.next())
        self.assertEqual(self.conn3, pool_iter.next())
        with self.assertRaises(StopIteration):
            pool_iter.next()

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

