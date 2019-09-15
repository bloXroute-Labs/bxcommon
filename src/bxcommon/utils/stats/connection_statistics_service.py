from bxcommon.utils.stats.statistics_event_service import StatisticsEventService
from bxutils.logging.log_record_type import LogRecordType
from bxutils import logging


class _ConnectionStatisticsService(StatisticsEventService):
    def __init__(self):
        super(_ConnectionStatisticsService, self).__init__()
        self.name = "ConnectionState"
        self.logger = logging.get_logger(LogRecordType.ConnectionState)


connection_stats = _ConnectionStatisticsService()
