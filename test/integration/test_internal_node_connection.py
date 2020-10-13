import time

from mock import MagicMock

from bxcommon import constants
from bxcommon.connections.connection_state import ConnectionState
from bxcommon.connections.internal_node_connection import InternalNodeConnection
from bxcommon.messages.bloxroute.hello_message import HelloMessage
from bxcommon.messages.bloxroute.pong_message import PongMessage
from bxcommon.test_utils import helpers
from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.utils.alarm_queue import AlarmQueue


class InternalNodeConnectionTest(AbstractTestCase):

    def setUp(self):
        self.connection = helpers.create_connection(InternalNodeConnection)
        self.connection.state = self.connection.state | ConnectionState.ESTABLISHED
        self.alarm_queue = AlarmQueue()
        self.connection.node.alarm_queue = self.alarm_queue

    def test_hello_schedules_pings(self):
        self.connection.msg_hello(HelloMessage(1, 1, helpers.generate_node_id()))

        self.assertEqual(1, len(self.alarm_queue.alarms))
        self.assertIsNotNone(self.connection.ping_alarm_id)

        self.assertEqual(self.alarm_queue.alarms[0], self.connection.ping_alarm_id)

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

        self.connection.msg_pong(PongMessage(1, 2))
        self.assertIsNone(self.connection.pong_timeout_alarm_id)

        time.time = MagicMock(return_value=time.time() + constants.PING_PONG_REPLY_TIMEOUT_S)
        self.connection.node.alarm_queue.fire_alarms()
        self.assertIsNone(self.connection.pong_timeout_alarm_id)
        self.assertTrue(self.connection.is_active())
