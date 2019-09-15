from collections import defaultdict
from datetime import datetime

from bxcommon import constants
from bxcommon.utils import memory_utils
from bxcommon.utils.stats.class_mem_stats import ClassMemStats
from bxcommon.utils.stats.statistics_service import StatsIntervalData, ThreadedStatisticsService
from bxutils.logging.log_record_type import LogRecordType
from bxutils import logging


class MemoryStatsIntervalData(StatsIntervalData):
    __slots__ = ["class_mem_stats"]

    def __init__(self, *args, **kwargs):
        super(MemoryStatsIntervalData, self).__init__(*args, **kwargs)
        self.class_mem_stats = defaultdict(ClassMemStats)


class MemoryStatsService(ThreadedStatisticsService):
    INTERVAL_DATA_CLASS = MemoryStatsIntervalData

    def __init__(self, interval=0):
        super(MemoryStatsService, self).__init__("MemoryStats", interval=interval, look_back=5, reset=False,
                                                 logger=logging.get_logger(LogRecordType.Memory))

    def set_node(self, node):
        super(MemoryStatsService, self).set_node(node)
        self.interval = node.opts.memory_stats_interval

    def add_mem_stats(self, class_name, network_num, obj, obj_name, obj_mem_info, object_item_count=None):
        mem_stats = self.interval_data.class_mem_stats[class_name]
        mem_stats.timestamp = datetime.utcnow()

        # If the object being analyzed doesn't have a length property
        if object_item_count is None:
            object_item_count = len(obj) if hasattr(obj, "__len__") else 0

        mem_stats.networks[network_num].analyzed_objects[obj_name].object_item_count = object_item_count
        mem_stats.networks[network_num].analyzed_objects[obj_name].object_size = obj_mem_info.size
        mem_stats.networks[network_num].analyzed_objects[obj_name].object_flat_size = obj_mem_info.flat_size
        mem_stats.networks[network_num].analyzed_objects[obj_name].is_actual_size = obj_mem_info.is_actual_size

    def get_info(self):
        # total_mem_usage is the peak mem usage fo the process (kilobytes on Linux, bytes on OS X)
        payload = dict(
            node_id=self.interval_data.node.opts.node_id,
            node_type=self.interval_data.node.opts.node_type,
            node_network_num=self.interval_data.node.opts.blockchain_network_num,
            node_address="%s:%d" % (
                self.interval_data.node.opts.external_ip,
                self.interval_data.node.opts.external_port
            ),
            total_mem_usage=memory_utils.get_app_memory_usage(),
            classes=self.interval_data.class_mem_stats
        )

        return payload

    def flush_info(self):
        self.node.dump_memory_usage()
        return super(MemoryStatsService, self).flush_info()

    def increment_mem_stats(self, class_name, network_num, obj, obj_name, obj_mem_info, object_item_count=None):
        mem_stats = self.interval_data.class_mem_stats[class_name]

        # If the object being analyzed doesn't have a length property
        if object_item_count is None:
            object_item_count = len(obj) if hasattr(obj, "__len__") else 0

        mem_stats.networks[network_num].analyzed_objects[obj_name].object_item_count += object_item_count
        mem_stats.networks[network_num].analyzed_objects[obj_name].object_size += obj_mem_info.size
        mem_stats.networks[network_num].analyzed_objects[obj_name].object_flat_size += obj_mem_info.flat_size
        mem_stats.networks[network_num].analyzed_objects[obj_name].is_actual_size = obj_mem_info.is_actual_size

    def reset_class_mem_stats(self, class_name):
        mem_stats = ClassMemStats()
        mem_stats.timestamp = datetime.utcnow()
        self.interval_data.class_mem_stats[class_name] = mem_stats


memory_statistics = MemoryStatsService(constants.MEMORY_STATS_INTERVAL_S)
