from collections import deque

from bxcommon.constants import THROUGHPUT_STATS_INTERVAL, THROUGHPUT_STATS_LOOK_BACK
from bxcommon.utils import logger
from bxcommon.utils.throughput.stats_interval import StatsInterval
from throughput_event import ThroughputEvent


class _ThroughputService(object):

    def __init__(self):
        self.throughput_stats = deque()
        self.max_look_back = THROUGHPUT_STATS_LOOK_BACK / THROUGHPUT_STATS_INTERVAL
        self.node = None
        self.stats_interval = None

    def set_node(self, node):
        self.node = node
        self.stats_interval = StatsInterval(node)

    def add_event(self, direction, msg_type, msg_size, peer_desc):
        # add new throughput event to current stats_interval
        self.stats_interval.add_throughput_event(ThroughputEvent(direction, msg_type, msg_size, peer_desc))

    def flush_stats(self):
        self.throughput_stats.append(self.stats_interval)
        logger.info("Interval throughput stats: {0}".format(self.stats_interval.get_json()))

        # Make sure we only have MAX_LOOK_BACK elements in the throughput_stats deque
        while len(self.throughput_stats) > self.max_look_back:
            # Remove the "oldest" element
            self.throughput_stats.popleft()

        # Start a new interval
        self.stats_interval = StatsInterval(self.node)
        return THROUGHPUT_STATS_INTERVAL


throughput_service = _ThroughputService()
