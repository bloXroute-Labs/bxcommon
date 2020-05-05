from typing import Optional

from bxcommon.utils.stats.stat_event_logic_flags import StatEventLogicFlags


class StatEventTypeSettings:
    def __init__(self, name: str, event_logic_flags: Optional[StatEventLogicFlags] = StatEventLogicFlags.NONE,
                 detailed_stat_event: Optional[bool] = False, priority: bool = False):
        self.name = name
        self.event_logic = event_logic_flags
        self.detailed_stat_event = detailed_stat_event
        self.priority = priority
