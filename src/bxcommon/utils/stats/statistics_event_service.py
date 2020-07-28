import datetime
from typing import Optional

from bxcommon.utils.stats.stat_event import StatEvent
from bxcommon.utils.stats.stat_event_type_settings import StatEventTypeSettings
from bxutils import logging
from bxutils.logging.log_level import LogLevel


# TODO: change default log level from STATS to info


class StatisticsEventService:
    def __init__(self) -> None:
        self.name = None
        self.log_level = LogLevel.STATS
        self.logger = logging.get_logger(__name__)
        self.priority_logger = logging.get_logger(__name__)
        self.node = None
        self.node_id = None

    def set_node(self, node) -> None:
        self.node = node
        assert node.opts is not None
        self.node_id = node.opts.node_id

    def log_event(self, event_settings: StatEventTypeSettings, object_id: str,
                  start_date_time: Optional[datetime.datetime], end_date_time: Optional[datetime.datetime], **kwargs):

        if start_date_time is None:
            start_date_time = datetime.datetime.utcnow()

        if end_date_time is None:
            end_date_time = start_date_time

        # pyre-fixme[6]: Expected `str` for 3rd param but got `None`.
        stat_event = StatEvent(event_settings, object_id, self.node_id, start_date_time, end_date_time, **kwargs)
        if event_settings.priority:
            self.priority_logger.log(self.log_level, {"data": stat_event, "type": self.name})
        else:
            self.logger.log(self.log_level, {"data": stat_event, "type": self.name})
