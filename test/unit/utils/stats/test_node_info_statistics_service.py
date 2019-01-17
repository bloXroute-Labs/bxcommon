from collections import deque

from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.test_utils.mocks.mock_node import MockNode
from bxcommon.utils.stats.node_info_service import node_info_statistics
from bxcommon.utils.stats.hooks import add_throughput_event, add_measurement
from bxcommon.test_utils.mocks.mock_connection import MockConnection
from bxcommon.connections.connection_pool import ConnectionPool

class NodeInfoServiceTests(AbstractTestCase):

    def setUp(self):
        self.node = MockNode("localhost", 8888)
        connection = MockConnection(1, ("localhost", 9999), MockNode("localhost", 9999))
        self.node.connection_pool = ConnectionPool()
        self.node.connection_pool.add(1, connection.peer_ip, connection.peer_port, connection)
        node_info_statistics.set_node(self.node)

    def test_info_statistics(self):
        info = node_info_statistics.get_info()
        self.assertTrue(info["node_peers"])
        self.assertEqual(info["external_port"], 8000)
