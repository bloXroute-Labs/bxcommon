from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.connections.connection_pool import ConnectionPool
from bxcommon.test_utils import helpers
from bxcommon.test_utils.mocks.mock_connection import MockConnection
from bxcommon.test_utils.mocks.mock_node import MockNode
from bxcommon.utils.stats.node_info_service import node_info_statistics


class NodeInfoServiceTests(AbstractTestCase):

    def setUp(self):
        self.node = MockNode(helpers.get_common_opts(8888))
        # noinspection PyTypeChecker
        connection = helpers.create_connection(MockConnection, self.node, port=9999)
        self.node.connection_pool = ConnectionPool()
        self.node.connection_pool.add(1, connection.peer_ip, connection.peer_port, connection)
        node_info_statistics.set_node(self.node)

    def test_info_statistics(self):
        info = node_info_statistics.get_info()
        self.assertTrue(info["node_peers"])
        self.assertEqual(info["external_port"], 8888)
