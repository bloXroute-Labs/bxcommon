from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.test_utils.mocks.mock_node import MockNode
from bxcommon.test_utils.mocks.mock_connection import MockConnection
from bxcommon.test_utils.mocks.mock_socket_connection import MockSocketConnection
from bxcommon.utils import memory_utils
from bxcommon.utils.memory_utils import ObjectSize
from bxcommon.test_utils.helpers import get_common_opts
from collections import deque
import platform


class MemoryUtilsTest(AbstractTestCase):

    def test_get_app_memory_usage(self):
        memory_usage = memory_utils.get_app_memory_usage()

        # verify that memory usage is reported in MB.
        # Expected to me less than 100 MB but greater than 1 MB
        self.assertLess(memory_usage, 100 * 1024 * 1024)
        self.assertGreater(memory_usage, 1 * 1024 * 1024)

    def test_get_object_size(self):
        mock_node = MockNode(get_common_opts(1234))
        object_size = memory_utils.get_object_size(mock_node)

        self.assertIsInstance(object_size, ObjectSize)
        self.assertTrue(object_size.size > 0)
        self.assertTrue(object_size.flat_size > 0)
        self.assertTrue(object_size.is_actual_size)
        self.assertEqual(0, len(object_size.references))

    def test_get_detailed_object_size(self):
        mock_node = MockNode(get_common_opts(1234))
        object_size = memory_utils.get_detailed_object_size(mock_node, 10000)
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

    def test_get_special_size(self):
        m = memoryview(b"000"*1000)
        m1 = memoryview(b"000"*1000)
        m2 = memoryview(b"1")
        adt_size = memory_utils.getsizeof(m)
        adt_size2 = memory_utils.getsizeof(m2)
        object_size = memory_utils.get_object_size(m)
        object_size2 = memory_utils.get_object_size(m2)
        actual_size = memory_utils.get_special_size(m).size
        d = deque("0" * 64)
        if "Darwin" not in platform.platform():
            self.assertEqual(adt_size, adt_size2)  # memoryviews are 200 byte ADTs
            self.assertEqual(object_size.size, object_size2.size)  # object_size cant calculate contents
            self.assertEqual(memory_utils.getsizeof(d), 1160)  # Size of deque ADT
            self.assertEqual(memory_utils.get_special_size(d).size, 4744)  # Actual size of deque ADT + contents
            self.assertEqual(actual_size,
                             m.nbytes + adt_size)  # get_special_size actually calculates contents + ADT size
            d.append("0")
            self.assertEqual(memory_utils.getsizeof(d), 1160)  # Didn't register change
            self.assertEqual(memory_utils.get_special_size(d).size, 4800)  # Actual size of deque ADT + contents
            d.append(m)  # Adding the memoryview to the deque to test recursion
            self.assertEqual(memory_utils.getsizeof(d), 1160)  # Didn't register change
            self.assertEqual(memory_utils.get_special_size(d).size, 4800 + actual_size)
        else:
            self.assertEqual(adt_size, 200)  # memoryviews are 200 byte ADTs
            self.assertEqual(object_size.size, 200)  # object_size cant calculate contents
            self.assertEqual(memory_utils.getsizeof(d), 1168)  # Size of deque ADT
            self.assertEqual(memory_utils.get_special_size(d).size, 4752)  # Actual size of deque ADT + contents
            self.assertEqual(actual_size,
                             m.nbytes + adt_size)  # get_special_size actually calculates contents + ADT size
            d.append("0")
            self.assertEqual(memory_utils.getsizeof(d), 1168)  # Didn't register change
            self.assertEqual(memory_utils.get_special_size(d).size, 4808)  # Actual size of deque ADT + contents
            d.append(m)  # Adding the memoryview to the deque to test recursion
            self.assertEqual(memory_utils.getsizeof(d), 1168)  # Didn't register change
            self.assertEqual(memory_utils.get_special_size(d).size, 4808 + actual_size)
        full_size, ids = memory_utils.get_special_size(m)
        self.assertTrue(ids)
        self.assertTrue(id(m) in ids and id(m.obj) in ids)
        mem_size, ids = memory_utils.get_special_size(m1, ids)
        self.assertLess(mem_size, full_size)
        self.assertTrue(id(m1) in ids and id(m1.obj) in ids)

    def test_add_special_objects(self):
        node1 = MockNode(get_common_opts(1001, external_ip="128.128.128.128"))
        conn1 = MockConnection(MockSocketConnection(1), ("123.123.123.123", 1000), node1)
        conn1.inputbuf.add_bytes(bytearray(b"0000"*10))
        conn1.outputbuf.prepend_msgbytes(bytearray(b"1111" * 100))
        total_special_size, ids = memory_utils.get_special_size(conn1)

        self.assertTrue(ids)
        self.assertTrue(id(conn1.inputbuf.input_list) in ids)
        self.assertTrue(id(conn1.outputbuf.output_msgs) in ids)

        expected_special_size = memory_utils.get_special_size(conn1.inputbuf.input_list).size
        expected_special_size += memory_utils.get_special_size(conn1.outputbuf.output_msgs).size
        self.assertEqual(total_special_size, expected_special_size)

        s, s_id = memory_utils.get_special_size(conn1.outputbuf.output_msgs)
        self.assertNotEqual(s, 0)
        s, ids = memory_utils.get_special_size(conn1.outputbuf.output_msgs, ids)
        self.assertEqual(s, 0)
