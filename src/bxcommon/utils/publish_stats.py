from bxcommon.utils import logger, json_utils


def publish_stats(stats_name, stats_payload):
    logger.statistics({"data": stats_payload, "type": stats_name})
