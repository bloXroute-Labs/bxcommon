from bxcommon.utils.stats.memory_statistics_service import memory_statistics
from bxcommon.utils.stats.throughput_service import throughput_statistics


def add_throughput_event(direction, msg_type, msg_size, peer_desc):
    return throughput_statistics.add_event(direction, msg_type, msg_size, peer_desc)


def add_measurement(peer_desc, measure_type, measure_value):
    return throughput_statistics.add_measurement(peer_desc, measure_type, measure_value)


def add_obj_mem_stats(class_name, network_num, obj, obj_name, obj_mem_info, object_item_count=None):
    return memory_statistics.add_mem_stats(class_name, network_num, obj, obj_name, obj_mem_info, object_item_count)
