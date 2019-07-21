from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.utils.collections.priority_queue import ObjectPriority, PriorityQueue


class PriorityQueueTest(AbstractTestCase):

    def setUp(self):
        super(PriorityQueueTest, self).setUp()
        self.priority_queue: PriorityQueue[int] = PriorityQueue(True)
        self.items = [5, 3, 88, 4, 0, 55, 1]

    def test_update_priority(self):
        for item in self.items:
            op = ObjectPriority(lambda i: i, item)
            self.priority_queue.add(op)
        self.assertEqual(self.items, list(self.priority_queue._items_dict.keys()))
        self.priority_queue.update_priority()
        sorted_list = sorted(self.items.copy(), reverse=True)
        self.assertEqual(sorted_list, list(self.priority_queue._items_dict.keys()))
