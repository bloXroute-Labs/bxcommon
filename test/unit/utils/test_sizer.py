from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.test_utils.mocks.mock_node import MockNode
from bxcommon.utils import memory_utils
from bxcommon.utils.sizer import Sizer
from bxcommon.test_utils.helpers import get_common_opts


class SizerTest(AbstractTestCase):

    def test_sizer(self):
        s = Sizer()
        node1 = MockNode(get_common_opts(1001, external_ip="128.128.128.128"))
        s.set_excluded_asizer("bxcommon.test_utils.mocks.mock_node.MockNode")
        self.assertGreater(memory_utils.get_object_size(node1).size, 0)
        self.assertEqual(memory_utils.get_object_size(node1, sizer=s.sizer).size, 0)
