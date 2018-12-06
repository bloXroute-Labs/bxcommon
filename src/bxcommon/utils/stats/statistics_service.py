from collections import deque
from datetime import datetime
from bxcommon.utils.publish_stats import publish_stats


# TODO replace with dataclass
class StatsIntervalData(object):
    def __init__(self):
        self.node = None
        self.end_time = None
        self.node_id = None
        self.start_time = None


class StatisticsService(object):
    def __init__(self, interval=0, look_back=1, reset=False):
        self.history = deque(maxlen=look_back)
        self.node = None
        self.name = None
        self.interval_data = None
        self.interval = interval
        self.reset = reset

    def set_node(self, node):
        self.node = node
        self.create_interval_data_object()

    def create_interval_data_object(self):
        self.interval_data = StatsIntervalData()
        self.interval_data.node = self.node
        self.interval_data.node_id = self.node.opts.node_id
        self.interval_data.start_time = datetime.utcnow()

    def get_info(self):
        if self.node is None:
            raise ValueError
        return self.interval_data

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

