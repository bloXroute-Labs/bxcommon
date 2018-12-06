from bxcommon.utils.stats.throughput_service import throughput_statistics


def add_throughput_event(direction, msg_type, msg_size, peer_desc):
    return throughput_statistics.add_event(direction, msg_type, msg_size, peer_desc)
