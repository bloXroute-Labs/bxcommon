import datetime
from typing import Optional, List, TYPE_CHECKING

from bxutils import logging
from bxutils.logging.log_level import LogLevel

from bxcommon.utils.stats.stat_event import StatEvent
from bxcommon.utils.stats.stat_event_type_settings import StatEventTypeSettings

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from bxcommon.connections.abstract_connection import AbstractConnection


# TODO: change default log level from STATS to info


class StatisticsEventService:
    def __init__(self) -> None:
        self.name = None
        self.log_level = LogLevel.STATS
        self.logger = logging.get_logger(__name__)
        self.priority_logger = logging.get_logger(__name__)
        self.node = None
        self.node_id: Optional[str] = None

    def set_node(self, node) -> None:
        self.node = node
        assert node.opts is not None
        self.node_id = node.opts.node_id

    def log_event(
        self,
        event_settings: StatEventTypeSettings,
        object_id: str,
        start_date_time: Optional[datetime.datetime],
        end_date_time: Optional[datetime.datetime],
        peers: Optional[List["AbstractConnection"]] = None,
        **kwargs
    ) -> None:
        node_id = self.node_id
        assert node_id is not None

        if start_date_time is None:
            start_date_time = datetime.datetime.utcnow()

        if end_date_time is None:
            end_date_time = start_date_time

        stat_event = StatEvent(
            event_settings, object_id, node_id, start_date_time, end_date_time, peers, **kwargs
        )
        if event_settings.priority:
            self.priority_logger.log(self.log_level, {"data": stat_event, "type": self.name})
        else:
            self.logger.log(self.log_level, {"data": stat_event, "type": self.name})
