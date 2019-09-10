from bxutils import logging

logger = logging.get_logger(__name__)


def publish_stats(stats_name, stats_payload):
    logger.statistics({"data": stats_payload, "type": stats_name})
