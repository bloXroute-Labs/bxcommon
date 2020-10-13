from typing import Callable, Optional, cast, List, Tuple

from bxcommon.utils.alarm_queue import AlarmQueue, AlarmId, Alarm


class MockAlarmQueue(AlarmQueue):
    def __init__(self) -> None:
        super().__init__()
        self.alarms = cast(
            List[Tuple[float, Callable]],
            self.alarms
        )

    # pylint: disable=arguments-differ
    def register_alarm(
        self, fire_delay: float, fn: Callable, *args, _alarm_name: Optional[str] = None, **kwargs
    ) -> AlarmId:
        self.alarms.append((fire_delay, fn))
        return AlarmId(fire_delay, 1, Alarm(fn, fire_delay))
