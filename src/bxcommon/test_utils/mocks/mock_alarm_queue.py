from bxcommon.utils.alarm_queue import AlarmQueue


class MockAlarmQueue(AlarmQueue):
    def __init__(self):
        self.alarms = []

    def register_alarm(self, fire_delay, fn, *args):
        self.alarms.append((fire_delay, fn))
