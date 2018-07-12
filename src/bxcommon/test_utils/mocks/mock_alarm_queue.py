class MockAlarmQueue():
    def __init__(self):
        self.alarms = []

    def register_alarm(self, fire_delay, fn, *args):
        self.alarms.append((fire_delay,fn))
