from typing import List, Any

from bxcommon.utils import logger
from bxcommon.utils.expiration_queue import ExpirationQueue


class ExpiringSet(object):
    """
    Set with expiration time.

    For determining if items are in the set, use "if item in expiring_set.contents".
    __contains__ is intentionally not overwritten. This is a performance critical class,
    and we're avoiding extra function call overhead.
    """

    def __init__(self, alarm_queue, expiration_time_s, log_removal=False):
        self.contents = set()
        self._alarm_queue = alarm_queue
        self._expiration_queue = ExpirationQueue(expiration_time_s)
        self._expiration_time = expiration_time_s
        self._log_removal = log_removal

    def __contains__(self, item):
        return item in self.contents

    def __len__(self):
        return len(self.contents)

    def add(self, item):
        self.contents.add(item)
        self._expiration_queue.add(item)
        self._alarm_queue.register_approx_alarm(self._expiration_time * 2, self._expiration_time, self.cleanup)

    def get_recent_items(self, count: int) -> List[Any]:
        items = []
        entries = reversed(self._expiration_queue.queue.keys())

        try:
            for i in range(count):
                items.append(next(entries))
        except StopIteration as _e:
            logger.warn("Attempted to fetch {} entries, but only {} existed.", count, len(items))

        return items

    def cleanup(self):
        self._expiration_queue.remove_expired(remove_callback=self._safe_remove_item)
        return 0

    def _safe_remove_item(self, item):
        if self._log_removal:
            logger.info("Removing {} from expiring set.", item)
        if item in self.contents:
            self.contents.remove(item)

