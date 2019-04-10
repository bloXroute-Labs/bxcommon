import datetime
from typing import Optional

from bxcommon.utils import publish_stats
from bxcommon.utils.stats.stat_event import StatEvent
from bxcommon.utils.stats.stat_event_type_settings import StatEventTypeSettings


class StatisticsEventService(object):
    def __init__(self):
        self.name = None
        self.node = None
        self.node_id = None

    def set_node(self, node):
        self.node = node
        self.node_id = self.node.opts.node_id

    def log_event(self, event_settings: StatEventTypeSettings, object_id: str,
                  start_date_time: Optional[datetime.datetime], end_date_time: Optional[datetime.datetime], **kwargs):

        if start_date_time is None:
            start_date_time = datetime.datetime.utcnow()

        if end_date_time is None:
            end_date_time = start_date_time

        stat_event = StatEvent(event_settings, object_id, self.node_id, start_date_time, end_date_time, **kwargs)
        publish_stats.publish_stats(self.name, stat_event)
