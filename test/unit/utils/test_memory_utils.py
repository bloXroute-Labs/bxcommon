from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.test_utils.mocks.mock_node import MockNode
from bxcommon.utils import memory_utils
from bxcommon.utils.memory_utils import ObjectSize


class MemoryUtilsTest(AbstractTestCase):

    def test_get_app_memory_usage(self):
        self.assertTrue(memory_utils.get_app_memory_usage() > 0)

    def get_object_size(self):
        mock_node = MockNode("127.0.0.1", 12345)
        object_size = memory_utils.get_object_size(mock_node)

        self.assertIsInstance(object_size, ObjectSize)
        self.assertTrue(object_size.size > 0)
        self.assertTrue(object_size.flat_size > 0)
        self.assertTrue(object_size.is_actual_size)
        self.assertEqual(0, len(object_size.references))

    def get_detailed_object_size(self):
        mock_node = MockNode("127.0.0.1", 12345)
        object_size = memory_utils.get_detailed_object_size(mock_node)

        self.assertIsInstance(object_size, ObjectSize)
        self.assertTrue(object_size.size > 0)
        self.assertTrue(object_size.flat_size > 0)
        self.assertTrue(object_size.is_actual_size)
        self.assertTrue(len(object_size.references) > 0)

        for ref in object_size.references:
            self.assertIsInstance(ref, ObjectSize)
            self.assertTrue(ref.size > 0)
            self.assertTrue(ref.flat_size > 0)
            self.assertTrue(ref.is_actual_size)
