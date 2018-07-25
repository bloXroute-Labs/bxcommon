import heapq
import time


class ExpirationQueue(object):
    def __init__(self, time_to_live_sec):
        self.time_to_live_sec = time_to_live_sec
        self.queue = []

    def add(self, item):
        heapq.heappush(self.queue, (time.time(), item))

    def remove_expired(self, current_time=None, remove_callback=None):
        if current_time is None:
            current_time = time.time()

        while self.queue and \
                current_time - self.queue[0][0] > self.time_to_live_sec:
            _, item = heapq.heappop(self.queue)

            if remove_callback is not None:
                remove_callback(item)

    def __len__(self):
        return len(self.queue)
