import datetime
from typing import Optional

from bxcommon.utils.stats.stat_event_type_settings import StatEventTypeSettings


class StatEvent:
    def __init__(self, event_settings: StatEventTypeSettings, event_subject_id: str, node_id: str,
                 start_date_time: datetime.datetime, end_date_time=Optional[datetime.datetime], **kwargs):
        self.event_name = event_settings.name
        self.event_logic = event_settings.event_logic
        self.event_subject_id = event_subject_id
        self.node_id = node_id
        self.start_date_time = start_date_time
        self.end_date_time = end_date_time if end_date_time is not None else start_date_time

        self.extra_data = kwargs
