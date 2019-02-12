import resource
from collections import defaultdict
from datetime import datetime

from bxcommon import constants
from bxcommon.utils.stats.class_mem_stats import ClassMemStats
from bxcommon.utils.stats.statistics_service import StatisticsService, StatsIntervalData


class MemoryStatsIntervalData(StatsIntervalData):
    __slots__ = ["class_mem_stats"]

    def __init__(self, *args, **kwargs):
        super(MemoryStatsIntervalData, self).__init__(*args, **kwargs)
        self.class_mem_stats = defaultdict(ClassMemStats)


class MemoryStatsService(StatisticsService):
    INTERVAL_DATA_CLASS = MemoryStatsIntervalData

    def __init__(self, interval=0):
        super(MemoryStatsService, self).__init__("MemoryStats", interval=interval, look_back=5, reset=False)

    def add_mem_stats(self, class_name, network_num, obj, obj_name, obj_mem_info):
        mem_stats = self.interval_data.class_mem_stats[class_name]
        mem_stats.timestamp = datetime.utcnow()

        # If the object being analyzed doesn't have a length property
        try:
            object_item_count = len(obj)
        except TypeError:
            object_item_count = -1

        mem_stats.networks[network_num].analyzed_objects[obj_name].object_item_count = object_item_count
        mem_stats.networks[network_num].analyzed_objects[obj_name].object_size = obj_mem_info.size
        mem_stats.networks[network_num].analyzed_objects[obj_name].object_flat_size = obj_mem_info.flat

    def get_info(self):
        # total_mem_usage is the peak mem usage fo the process (kilobytes on Linux, bytes on OS X)
        payload = dict(
            node_ip=self.interval_data.node.opts.node_id,
            node_type=self.interval_data.node.opts.node_type,
            node_network_num=self.interval_data.node.opts.blockchain_network_num,
            node_address="%s:%d" % (
                self.interval_data.node.opts.external_ip, self.interval_data.node.opts.external_port),
            total_mem_usage=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            classes=self.interval_data.class_mem_stats
        )

        return payload


memory_statistics = MemoryStatsService(constants.MEMORY_STATS_INTERVAL)
