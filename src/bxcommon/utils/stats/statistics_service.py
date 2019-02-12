from abc import ABCMeta, abstractmethod
from collections import deque
from datetime import datetime

from bxcommon.utils.publish_stats import publish_stats


# TODO replace with dataclass
class StatsIntervalData(object):
    __slots__ = ["node", "node_id", "start_time", "end_time"]

    def __init__(self, node, node_id, start_time=None, end_time=None):
        self.node = node
        self.node_id = node_id
        self.start_time = start_time
        self.end_time = end_time


class StatisticsService(object):
    """
    Abstract class of statistics services.
    """
    __metaclass__ = ABCMeta

    INTERVAL_DATA_CLASS = StatsIntervalData

    def __init__(self, name, interval=0, look_back=1, reset=False):
        self.history = deque(maxlen=look_back)
        self.node = None
        self.name = name
        self.interval_data = None
        self.interval = interval
        self.reset = reset

    @abstractmethod
    def get_info(self):
        """
        Constructs response object to be outputted on stat service set interval.
        :return: dictionary to be converted to JSON
        """
        pass

    def set_node(self, node):
        self.node = node
        self.create_interval_data_object()

    def create_interval_data_object(self):
        self.interval_data = self.INTERVAL_DATA_CLASS(self.node, self.node.opts.node_id, datetime.utcnow())

    def close_interval_data(self):
        self.interval_data.end_time = datetime.utcnow()
        self.history.append(self.interval_data)

    def flush_info(self):
        self.close_interval_data()
        publish_stats(stats_name=self.name, stats_payload=self.get_info())

        # Start a new interval data if non cumulative
        if self.reset:
            self.create_interval_data_object()
        return self.interval
