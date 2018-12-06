import json
from bxcommon.utils import logger
from bxcommon.utils.class_json_encoder import ClassJsonEncoder


def publish_stats(stats_name, stats_payload):
    logger.statistics("{0}".format(
        json.dumps({stats_name: stats_payload}, cls=ClassJsonEncoder)
        )
    )
