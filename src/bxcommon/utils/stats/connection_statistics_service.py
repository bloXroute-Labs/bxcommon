from bxcommon.utils.stats.statistics_event_service import StatisticsEventService
from bxutils import logging
from bxutils.logging.log_record_type import LogRecordType


class _ConnectionStatisticsService(StatisticsEventService):
    def __init__(self) -> None:
        super(_ConnectionStatisticsService, self).__init__()
        self.name = "ConnectionState"
        self.logger = logging.get_logger(LogRecordType.ConnectionState, __name__)


connection_stats = _ConnectionStatisticsService()
