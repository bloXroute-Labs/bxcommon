from bxcommon.utils.stats.statistics_event_service import StatisticsEventService


class _ConnectionStatisticsService(StatisticsEventService):
    def __init__(self):
        super(_ConnectionStatisticsService, self).__init__()
        self.name = "ConnectionState"


connection_stats = _ConnectionStatisticsService()
