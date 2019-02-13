import datetime
import json


class StatEvent:
    def __init__(self, event_name, event_subject_id, node_id, start_date_time, end_date_time=None, **kwargs):
        if not event_name:
            raise ValueError("event_name is required")

        if not event_name:
            raise ValueError("event_category is required")

        if not event_subject_id:
            raise ValueError("event_subject_id is required")

        if not node_id:
            raise ValueError("node_id is required")

        if not start_date_time:
            raise TypeError("start_date_time is required")

        self.event_name = event_name
        self.event_subject_id = event_subject_id
        self.node_id = node_id
        self.start_date_time = start_date_time
        self.end_date_time = end_date_time if end_date_time is not None else start_date_time

        self.extra_data = kwargs

    def to_json(self):
        return json.dumps(self.__dict__)