import time

from mock import MagicMock

from bxcommon import constants
from bxcommon.connections.connection_state import ConnectionState
from bxcommon.connections.internal_node_connection import InternalNodeConnection
from bxcommon.messages.bloxroute.pong_message import PongMessage
from bxcommon.test_utils import helpers
from bxcommon.test_utils.abstract_test_case import AbstractTestCase


class InternalNodeConnectionTest(AbstractTestCase):

    def setUp(self):
        self.connection = helpers.create_connection(InternalNodeConnection)
        self.connection.state = self.connection.state | ConnectionState.ESTABLISHED

    def test_pong_msg_timeout_pong_not_received(self):
        self.assertIsNone(self.connection.pong_timeout_alarm_id)
        self.assertTrue(self.connection.is_active())

        self.connection.send_ping()
        self.assertIsNotNone(self.connection.pong_timeout_alarm_id)

        time.time = MagicMock(return_value=time.time() + constants.PING_PONG_REPLY_TIMEOUT_S - 1)
        self.connection.node.alarm_queue.fire_alarms()
        self.assertIsNotNone(self.connection.pong_timeout_alarm_id)

        time.time = MagicMock(return_value=time.time() + constants.PING_PONG_REPLY_TIMEOUT_S)
        self.connection.node.alarm_queue.fire_alarms()
        self.assertIsNone(self.connection.pong_timeout_alarm_id)
        self.assertFalse(self.connection.is_active())

    def test_pong_msg_timeout_pong_received(self):
        self.assertIsNone(self.connection.pong_timeout_alarm_id)
        self.assertTrue(self.connection.is_active())

        self.connection.send_ping()
        self.assertIsNotNone(self.connection.pong_timeout_alarm_id)

        self.connection.msg_pong(PongMessage(1))
        self.assertIsNone(self.connection.pong_timeout_alarm_id)

        time.time = MagicMock(return_value=time.time() + constants.PING_PONG_REPLY_TIMEOUT_S)
        self.connection.node.alarm_queue.fire_alarms()
        self.assertIsNone(self.connection.pong_timeout_alarm_id)
        self.assertTrue(self.connection.is_active())
