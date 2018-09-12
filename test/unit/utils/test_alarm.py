from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.utils.alarm import Alarm


class AlarmTests(AbstractTestCase):

    def setUp(self):
        self.alarm = Alarm(self.function_to_pass, 1, 5)

    def test_init(self):
        self.assertEqual(self.alarm.args, (1, 5))
        self.assertEqual(self.alarm.fn, self.function_to_pass)

    def function_to_pass(self, first, second):
        return first + second

    def test_fire(self):
        self.assertEqual(self.alarm.fire(), 6)

