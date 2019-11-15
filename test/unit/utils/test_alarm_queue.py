import time

from mock import MagicMock

from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.utils.alarm_queue import AlarmQueue


class AlarmQueueTest(AbstractTestCase):

    def setUp(self):
        self.alarm_queue = AlarmQueue()

    def function_to_pass(self, first, second):
        return first + second

    def test_register_alarm(self):
        alarm_id = self.alarm_queue.register_alarm(1, self.function_to_pass, 1, 5)
        self.assertEqual(1, len(self.alarm_queue.alarms))
        self.assertEqual(1, self.alarm_queue.uniq_count)
        self.assertEqual(0, self.alarm_queue.alarms[0].count)
        self.assertEqual(0, alarm_id.count)

    def test_register_approx_alarm(self):
        self.alarm_queue.register_approx_alarm(1, 3, self.function_to_pass, 1, 5)
        self.assertEqual(1, len(self.alarm_queue.approx_alarms_scheduled[self.function_to_pass]))
        self.assertEqual(self.function_to_pass,
                         self.alarm_queue.approx_alarms_scheduled[self.function_to_pass][0].alarm.fn)

    def test_unregister_alarm(self):
        alarm_id1 = self.alarm_queue.register_alarm(1, self.function_to_pass, 1, 5)
        self.assertEqual(1, len(self.alarm_queue.alarms))
        alarm_id2 = self.alarm_queue.register_alarm(1, self.function_to_pass, 2, 9)
        self.assertEqual(2, len(self.alarm_queue.alarms))
        self.alarm_queue.unregister_alarm(alarm_id1)
        self.assertEqual(1, len(self.alarm_queue.alarms))
        self.alarm_queue.unregister_alarm(alarm_id2)
        self.assertEqual(0, len(self.alarm_queue.alarms))

    def test_fire_alarms(self):
        self.alarm_queue.register_alarm(1, self.function_to_pass, 0, 0)
        self.alarm_queue.register_alarm(5, self.function_to_pass, 0, 0)
        time.time = MagicMock(return_value=time.time() + 2)
        self.alarm_queue.fire_alarms()
        self.assertEqual(1, len(self.alarm_queue.alarms))

    def test_time_to_next_alarm(self):
        self.assertIsNone(self.alarm_queue.time_to_next_alarm())
        self.alarm_queue.register_alarm(1, self.function_to_pass, 1, 5)
        self.assertEqual(1, len(self.alarm_queue.alarms))
        self.assertLess(0, self.alarm_queue.time_to_next_alarm())
        time.time = MagicMock(return_value=time.time() + 2)
        self.assertGreater(0, self.alarm_queue.time_to_next_alarm())

    def test_fire_ready_alarms(self):
        self.alarm_queue.register_alarm(1, self.function_to_pass, 0, 0)
        self.alarm_queue.register_alarm(5, self.function_to_pass, 0, 0)
        time.time = MagicMock(return_value=time.time() + 2)
        time_to_next_alarm = self.alarm_queue.fire_ready_alarms()
        self.assertEqual(1, len(self.alarm_queue.alarms))
        self.assertLess(0, time_to_next_alarm)
