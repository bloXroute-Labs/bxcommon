from typing import Optional, Union

from bxcommon.network.network_direction import NetworkDirection
from bxcommon.utils.stats.measurement_type import MeasurementType
from bxcommon.utils.stats.memory_statistics_service import memory_statistics
from bxcommon.utils.stats.throughput_service import throughput_statistics


def add_throughput_event(
    direction: NetworkDirection,
    msg_type: str,
    msg_size: int,
    peer_desc: str,
    peer_id: Optional[str] = None,
):
    return throughput_statistics.add_event(direction, msg_type, msg_size, peer_desc, peer_id)


def add_measurement(
    peer_desc: str,
    measure_type: MeasurementType,
    measure_value: Union[float, int],
    peer_id: Optional[str] = None,
):
    return throughput_statistics.add_measurement(peer_desc, measure_type, measure_value, peer_id)


def add_obj_mem_stats(
    class_name,
    network_num,
    obj,
    obj_name,
    obj_mem_info,
    object_type=None,
    size_type=None,
    object_item_count=None,
):
    return memory_statistics.add_mem_stats(
        class_name,
        network_num,
        obj,
        obj_name,
        obj_mem_info,
        object_type,
        size_type,
        object_item_count,
    )


def increment_obj_mem_stats(
    class_name,
    network_num,
    obj,
    obj_name,
    obj_mem_info,
    object_type=None,
    size_type=None,
    object_item_count=None,
):
    return memory_statistics.increment_mem_stats(
        class_name,
        network_num,
        obj,
        obj_name,
        obj_mem_info,
        object_type,
        size_type,
        object_item_count,
    )


def reset_class_mem_stats(class_name):
    return memory_statistics.reset_class_mem_stats(class_name)
