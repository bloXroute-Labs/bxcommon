import time

from collections import OrderedDict


class ExpirationQueue(object):
    """
    Handles queue of item that need to be expired and removed from the queue over time
    """

    def __init__(self, time_to_live_sec):

        if time_to_live_sec < 0:
            raise ValueError("Time to live cannot be negative.")

        self.time_to_live_sec = time_to_live_sec
        self.queue = OrderedDict()

    def add(self, item):
        """
        Adds item to the queue
        :param item: item
        """
        self.queue[item] = time.time()

    def remove(self, item):
        """
        Removes item from expiration queue
        :param item: item to remove
        """
        if item in self.queue:
            del self.queue[item]

    def remove_expired(self, current_time=None, remove_callback=None):
        """
        Removes expired items from the queue
        :param current_time: time to use as current time for expiration
        :param remove_callback: reference to a callback function that is being called when item is removed
        """
        if current_time is None:
            current_time = time.time()

        while len(self.queue) > 0 and \
                current_time - self.get_oldest_item_timestamp() > self.time_to_live_sec:
            item, timestamp = self.queue.popitem(last=False)

            if remove_callback is not None:
                remove_callback(item)

    def get_oldest(self):
        """
        Returns the value of oldest item in the queue
        :return: value of oldest item
        """
        if not self.queue:
            return None

        return next(iter(self.queue.keys()))

    def get_oldest_item_timestamp(self):
        """
        Returns timestamp of the oldest item
        :return: timestamp of the oldest item
        """
        if len(self.queue) == 0:
            return None

        oldest_item = self.get_oldest()
        return self.queue[oldest_item]

    def remove_oldest(self, remove_callback=None):
        """
        Remove one oldest item from the queue
        :param remove_callback: reference to a callback function that is being called when item is removed
        """
        if len(self.queue) > 0:
            item, timestamp = self.queue.popitem(last=False)

            if remove_callback is not None:
                remove_callback(item)

    def __len__(self):
        return len(self.queue)
