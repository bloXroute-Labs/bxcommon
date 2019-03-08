import heapq
import time


class ExpirationQueue(object):
    """
    Handles queue of item that need to be expired and removed from the queue over time
    """

    def __init__(self, time_to_live_sec):

        if time_to_live_sec < 0:
            raise ValueError("Time to live cannot be negative.")

        self.time_to_live_sec = time_to_live_sec
        self.queue = []

    def add(self, item):
        """
        Adds item to the queue
        :param item: item
        """
        heapq.heappush(self.queue, (time.time(), item))

    def remove_expired(self, current_time=None, remove_callback=None):
        """
        Removes expired items from the queue
        :param current_time: time to use as current time for expiration
        :param remove_callback: reference to a callback function that is being called when item is removed
        """
        if current_time is None:
            current_time = time.time()

        while self.queue and \
                current_time - self.queue[0][0] > self.time_to_live_sec:
            _, item = heapq.heappop(self.queue)

            if remove_callback is not None:
                remove_callback(item)

    def get_oldest(self):
        """
        Returns the value of oldest item in the queue
        :return: value of oldest item
        """
        if not self.queue:
            return None

        return self.queue[0][1]

    def remove_oldest(self, remove_callback=None):
        """
        Remove one oldest item from the queue
        :param remove_callback: reference to a callback function that is being called when item is removed
        """
        if self.queue:
            _, item = heapq.heappop(self.queue)

            if remove_callback is not None:
                remove_callback(item)

    def __len__(self):
        return len(self.queue)
