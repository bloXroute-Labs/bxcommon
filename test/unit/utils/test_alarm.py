from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.utils.alarm import Alarm


class AlarmTests(AbstractTestCase):

    def setUp(self):
        self.args = (1, 5)
        self.alarm = Alarm(self.function_to_pass, 0, self.args[0], self.args[1])

    def function_to_pass(self, first, second):
        return first + second

    def test_fire(self):
        self.assertEqual(6, self.alarm.fire())
