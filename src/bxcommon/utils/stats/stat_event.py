import datetime

from typing import Optional, List, TYPE_CHECKING
from collections import defaultdict

from bxcommon.utils.stats import stats_format
from bxcommon.utils.stats.stat_event_type_settings import StatEventTypeSettings

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from bxcommon.connections.abstract_connection import AbstractConnection


class StatEvent:
    def __init__(
        self,
        event_settings: StatEventTypeSettings,
        event_subject_id: str,
        node_id: str,
        start_date_time: datetime.datetime,
        end_date_time: Optional[datetime.datetime] = None,
        peers: Optional[List["AbstractConnection"]] = None,
        **kwargs
    ):
        self.event_name = event_settings.name
        self.event_logic = event_settings.event_logic
        self.event_subject_id = event_subject_id
        self.node_id = node_id
        self.start_date_time = start_date_time
        self.end_date_time = end_date_time if end_date_time is not None else start_date_time
        self.extra_data = kwargs
        if peers:
            peer_ids = defaultdict(list)
            for peer in peers:
                if peer and peer.peer_id:
                    peer_ids[peer.CONNECTION_TYPE.format_short()].append(peer.peer_id)
            self.extra_data["peer_ids"] = peer_ids
            self.extra_data["peers"] = stats_format.connections(peers)
