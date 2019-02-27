import time

from mock import MagicMock

from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.utils.alarm_queue import AlarmQueue
from bxcommon.utils.expiring_set import ExpiringSet


class ExpiringSetTest(AbstractTestCase):

    ALARM_QUEUE = AlarmQueue()
    EXPIRATION_TIME_S = 1

    def setUp(self):
        self.sut = ExpiringSet(self.ALARM_QUEUE, self.EXPIRATION_TIME_S)

    def test_cleanup(self):
        test_item = "dummy_text"
        self.sut.add(test_item)
        self.assertTrue(test_item in self.sut.contents)

        time.time = MagicMock(return_value=time.time() + self.EXPIRATION_TIME_S + 1)
        self.ALARM_QUEUE.fire_alarms()
        self.assertFalse(test_item in self.sut.contents)

    def test_cleanup__not_existing_item(self):
        test_item = "dummy_text"
        self.sut.add(test_item)
        self.assertTrue(test_item in self.sut.contents)

        self.sut.contents.remove(test_item)
        self.assertFalse(test_item in self.sut.contents)

        time.time = MagicMock(return_value=time.time() + self.EXPIRATION_TIME_S + 1)
        self.ALARM_QUEUE.fire_alarms()
        self.assertFalse(test_item in self.sut.contents)