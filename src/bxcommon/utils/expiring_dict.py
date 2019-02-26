from bxcommon.utils.expiration_queue import ExpirationQueue


class ExpiringDict(object):
    """
    Set with expiration time.

    For determining if items are in the set, use "if item in expiring_set.contents".
    __contains__ is intentionally not overwritten. This is a performance critical class,
    and we're avoiding extra function call overhead.
    """

    def __init__(self, alarm_queue, expiration_time_s):
        self.contents = dict()
        self._alarm_queue = alarm_queue
        self._expiration_queue = ExpirationQueue(expiration_time_s)
        self._expiration_time = expiration_time_s

    def add(self, key, value):
        self.contents[key] = value
        self._expiration_queue.add(key)
        self._alarm_queue.register_approx_alarm(self._expiration_time * 2, self._expiration_time, self.cleanup)

    def cleanup(self):
        self._expiration_queue.remove_expired(remove_callback=self.remove_item)
        return 0

    def remove_item(self, key):
        if key in self.contents:
            del self.contents[key]
