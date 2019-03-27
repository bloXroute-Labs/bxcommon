from bxcommon.utils import logger


def publish_stats(stats_name, stats_payload):
    logger.statistics({"data": stats_payload, "type": stats_name})
