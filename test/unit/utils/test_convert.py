from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.utils import convert


class ConvertTests(AbstractTestCase):

    def test_str_to_bool(self):
        self.assertTrue(convert.str_to_bool("True"))
        self.assertTrue(convert.str_to_bool("true"))
        self.assertTrue(convert.str_to_bool("1"))
        self.assertFalse(convert.str_to_bool("False"))
        self.assertFalse(convert.str_to_bool("false"))
        self.assertFalse(convert.str_to_bool("0"))
        self.assertFalse(convert.str_to_bool("dummy_text"))
        self.assertFalse(convert.str_to_bool(None))
