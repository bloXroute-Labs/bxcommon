from bxcommon import constants
from bxcommon.connections.abstract_connection import AbstractConnection
from bxcommon.connections.connection_pool import ConnectionPool
from bxcommon.connections.connection_state import ConnectionState
from bxcommon.connections.connection_type import ConnectionType
from bxcommon.constants import LOCALHOST, ALL_NETWORK_NUM
from bxcommon.messages.bloxroute.abstract_broadcast_message import AbstractBroadcastMessage
from bxcommon.messages.bloxroute.broadcast_message import BroadcastMessage
from bxcommon.services.broadcast_service import BroadcastService, BroadcastOptions
from bxcommon.test_utils import helpers
from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.test_utils.mocks.mock_connection import MockConnection
from bxcommon.test_utils.mocks.mock_node import MockNode
from bxcommon.test_utils.mocks.mock_socket_connection import MockSocketConnection
from bxcommon.utils.object_hash import Sha256Hash


class TestBroadcastService(BroadcastService[AbstractBroadcastMessage, AbstractConnection]):

    def should_broadcast_to_connection(self, message: AbstractBroadcastMessage, connection: AbstractConnection) \
            -> bool:
        return connection.network_num in [constants.ALL_NETWORK_NUM, message.network_num()]


class BroadcastServiceTest(AbstractTestCase):
    def setUp(self) -> None:
        self.node = MockNode(helpers.get_common_opts(8000))
        self.connection_pool = ConnectionPool()
        self.sut = TestBroadcastService(self.connection_pool)

    def _add_connection(self, fileno: int, port: int, network_num: int,
                        connection_type=MockConnection.CONNECTION_TYPE) -> MockConnection:
        conn = MockConnection(MockSocketConnection(fileno), (LOCALHOST, port), self.node)
        conn.network_num = network_num
        conn.state = ConnectionState.ESTABLISHED
        conn.CONNECTION_TYPE = connection_type

        self.connection_pool.add(fileno, LOCALHOST, port, conn)
        return conn

    def test_broadcast_to_network_numbers(self):
        all_matching_network_num = self._add_connection(0, 9000, ALL_NETWORK_NUM)
        matching_network_num = self._add_connection(1, 9001, 1)
        not_matching_network_num = self._add_connection(2, 9002, 2)

        message = BroadcastMessage(Sha256Hash(helpers.generate_hash()), 1, "", False,
                                   helpers.generate_bytearray(250))
        self.sut.broadcast(message, BroadcastOptions(connection_types=[MockConnection.CONNECTION_TYPE]))

        self.assertIn(message, all_matching_network_num.enqueued_messages)
        self.assertIn(message, matching_network_num.enqueued_messages)
        self.assertNotIn(message, not_matching_network_num.enqueued_messages)

    def test_broadcast_to_connection_type(self):
        relay_all_conn = self._add_connection(0, 9000, ALL_NETWORK_NUM, ConnectionType.RELAY_ALL)
        relay_block_conn = self._add_connection(1, 9001, ALL_NETWORK_NUM, ConnectionType.RELAY_BLOCK)
        relay_transaction_conn = self._add_connection(2, 9002, ALL_NETWORK_NUM, ConnectionType.RELAY_TRANSACTION)
        gateway_conn = self._add_connection(3, 9003, ALL_NETWORK_NUM, ConnectionType.GATEWAY)

        block_message = BroadcastMessage(Sha256Hash(helpers.generate_hash()), ALL_NETWORK_NUM, "", False,
                                         helpers.generate_bytearray(250))
        self.sut.broadcast(block_message, BroadcastOptions(connection_types=[ConnectionType.RELAY_BLOCK]))

        tx_message = BroadcastMessage(Sha256Hash(helpers.generate_hash()), ALL_NETWORK_NUM, "", False,
                                      helpers.generate_bytearray(250))
        self.sut.broadcast(tx_message, BroadcastOptions(connection_types=[ConnectionType.RELAY_TRANSACTION]))

        gateway_message = BroadcastMessage(Sha256Hash(helpers.generate_hash()), ALL_NETWORK_NUM, "", False,
                                           helpers.generate_bytearray(250))
        self.sut.broadcast(gateway_message, BroadcastOptions(connection_types=[ConnectionType.GATEWAY]))

        self.assertIn(block_message, relay_all_conn.enqueued_messages)
        self.assertIn(block_message, relay_block_conn.enqueued_messages)
        self.assertNotIn(block_message, relay_transaction_conn.enqueued_messages)
        self.assertNotIn(block_message, gateway_conn.enqueued_messages)

        self.assertIn(tx_message, relay_all_conn.enqueued_messages)
        self.assertNotIn(tx_message, relay_block_conn.enqueued_messages)
        self.assertIn(tx_message, relay_transaction_conn.enqueued_messages)
        self.assertNotIn(tx_message, gateway_conn.enqueued_messages)

        self.assertNotIn(gateway_message, relay_all_conn.enqueued_messages)
        self.assertNotIn(gateway_message, relay_block_conn.enqueued_messages)
        self.assertNotIn(gateway_message, relay_transaction_conn.enqueued_messages)
        self.assertIn(gateway_message, gateway_conn.enqueued_messages)
