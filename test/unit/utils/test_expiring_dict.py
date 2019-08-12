import time
import unittest

from mock import MagicMock

from bxcommon.utils.expiring_dict import ExpiringDict
from bxcommon.utils.alarm_queue import AlarmQueue


class ExpiringDictTests(unittest.TestCase):
    EXPIRATION_TIME_S = 1

    def setUp(self):
        self.ALARM_QUEUE = AlarmQueue()
        self.e_dict = ExpiringDict(self.ALARM_QUEUE, self.EXPIRATION_TIME_S)

    def test_cleanup(self):

        kv1 = (1, 2)
        kv2 = (3, 4)
        kv3 = (5, 6)
        kv4 = (7, 8)
        kv5 = ("str1", 1)
        kv6 = ("str2", 2)

        # adding first 2 items to the dict
        self.e_dict.add(kv1[0], kv1[1])
        self.e_dict.add(kv2[0], kv2[1])

        time.time = MagicMock(return_value=time.time() + self.EXPIRATION_TIME_S+1)

        self.assertEqual(len(self.e_dict.contents), 2)
        self.assertTrue(kv1[0] in self.e_dict.contents)
        self.assertTrue(kv2[0] in self.e_dict.contents)
        self.assertEqual(self.e_dict.contents[kv1[0]], kv1[1])
        self.assertEqual(self.e_dict.contents[kv2[0]], kv2[1])

        # adding last 2 items to the dict
        self.e_dict.add(kv3[0], kv3[1])
        self.e_dict.add(kv4[0], kv4[1])
        self.e_dict.add(kv5[0], kv5[1])
        self.e_dict.add(kv6[0], kv6[1])

        self.ALARM_QUEUE.fire_alarms()

        # first 2 items are expired, last two have not
        self.assertFalse(kv1[0] in self.e_dict.contents)
        self.assertFalse(kv2[0] in self.e_dict.contents)
        self.assertTrue(kv3[0] in self.e_dict.contents)
        self.assertTrue(kv4[0] in self.e_dict.contents)
        self.assertTrue(kv5[0] in self.e_dict.contents)
        self.assertTrue(kv6[0] in self.e_dict.contents)

    def test_remove_item(self):

        kv1 = (1, 2)
        self.e_dict.add(kv1[0], kv1[1])
        self.assertTrue(kv1[0] in self.e_dict.contents)
        self.e_dict.remove_item(kv1[0])
        self.assertFalse(kv1[0] in self.e_dict.contents)

    def test_cleanup__not_existing_item(self):

        kv1 = (1, 2)
        self.e_dict.add(kv1[0], kv1[1])
        self.assertTrue(kv1[0] in self.e_dict.contents)
        self.e_dict.remove_item(kv1[0])
        self.assertFalse(kv1[0] in self.e_dict.contents)

        time.time = MagicMock(return_value=time.time() + self.EXPIRATION_TIME_S + 1)

        self.ALARM_QUEUE.fire_alarms()

        self.assertFalse(kv1[0] in self.e_dict.contents)
