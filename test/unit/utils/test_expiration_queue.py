import time
import unittest

from mock import MagicMock

from bxcommon.utils.expiration_queue import ExpirationQueue


class ExpirationQueueTests(unittest.TestCase):
    def setUp(self):
        self.time_to_live = 60
        self.queue = ExpirationQueue(self.time_to_live)
        self.removed_items = []

    def test_expiration_queue(self):
        # adding 2 items to the queue with 1 second difference
        item1 = 1
        item2 = 2

        self.queue.add(item1)
        time_1_added = time.time()

        time.time = MagicMock(return_value=time.time() + 1)

        self.queue.add(item2)
        time_2_added = time.time()

        self.assertEqual(len(self.queue), 2)
        self.assertEqual(int(time_1_added), int(self.queue.get_oldest_item_timestamp()))
        self.assertEqual(item1, self.queue.get_oldest())

        # check that nothing is removed from queue before the first item expires
        self.queue.remove_expired(time_1_added + self.time_to_live / 2, remove_callback=self._remove_item)
        self.assertEqual(len(self.queue), 2)
        self.assertEqual(len(self.removed_items), 0)

        # check that first item removed after first item expired
        self.queue.remove_expired(time_1_added + self.time_to_live + 1, remove_callback=self._remove_item)
        self.assertEqual(len(self.queue), 1)
        self.assertEqual(len(self.removed_items), 1)
        self.assertEqual(self.removed_items[0], item1)
        self.assertEqual(int(time_2_added), int(self.queue.get_oldest_item_timestamp()))
        self.assertEqual(item2, self.queue.get_oldest())

        # check that second item is removed after second item expires
        self.queue.remove_expired(time_2_added + self.time_to_live + 1, remove_callback=self._remove_item)
        self.assertEqual(len(self.queue), 0)
        self.assertEqual(len(self.removed_items), 2)
        self.assertEqual(self.removed_items[0], item1)
        self.assertEqual(self.removed_items[1], item2)

    def test_remove_oldest_item(self):
        items_count = 10

        for i in range(items_count):
            self.queue.add(i)

        self.assertEqual(items_count, len(self.queue))

        removed_items_1 = []

        for i in range(items_count):
            self.assertEqual(i, self.queue.get_oldest())
            self.queue.remove_oldest(removed_items_1.append)
            self.queue.add(1000 + i)

        for i in range(items_count):
            self.assertEqual(i, removed_items_1[i])

        self.assertEqual(items_count, len(self.queue))

        removed_items_2 = []

        for i in range(items_count):
            self.assertEqual(i + 1000, self.queue.get_oldest())
            self.queue.remove_oldest(removed_items_2.append)

        for i in range(items_count):
            self.assertEqual(i + 1000, removed_items_2[i])

        self.assertEqual(0, len(self.queue))

    def test_remove_not_oldest_item(self):
        # adding 2 items to the queue with 1 second difference
        item1 = 9
        item2 = 5

        self.queue.add(item1)
        time_1_added = time.time()

        time.time = MagicMock(return_value=time.time() + 1)

        self.queue.add(item2)

        self.assertEqual(len(self.queue), 2)
        self.assertEqual(int(time_1_added), int(self.queue.get_oldest_item_timestamp()))
        self.assertEqual(item1, self.queue.get_oldest())

        self.queue.remove(item2)
        self.assertEqual(len(self.queue), 1)
        self.assertEqual(int(time_1_added), int(self.queue.get_oldest_item_timestamp()))
        self.assertEqual(item1, self.queue.get_oldest())

    def _remove_item(self, item):
        self.removed_items.append(item)
