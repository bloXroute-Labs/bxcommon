import socket

from mock import MagicMock

from bxcommon.connections.abstract_node import AbstractNode
from bxcommon.network.socket_connection import SocketConnection
from bxcommon.network.socket_connection_state import SocketConnectionState
from bxcommon.test_utils import helpers
from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.test_utils.mocks.mock_connection import MockConnection


class SocketConnectionTest(AbstractTestCase):
    def setUp(self) -> None:
        self.socket_instance = MagicMock(spec=socket.socket)
        self.socket_instance.fileno = MagicMock(return_value=1)
        self.node = AbstractNode(helpers.get_common_opts(1234))
        self.sut = SocketConnection(self.socket_instance, self.node, False)
        self.connection = helpers.create_connection(MockConnection, self.node, from_me=True)
        self.connection.socket_connection = self.sut
