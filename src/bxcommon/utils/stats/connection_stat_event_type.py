from bxcommon.utils.stats.stat_event_type_settings import StatEventTypeSettings


class ConnectionStateEventType:

    REGISTER_PENDING = StatEventTypeSettings("ConnectionRegisterPending")
    BUCKET_DEPLETED = StatEventTypeSettings("ConnectionBucketDepleted")
    TIMED_OUT = StatEventTypeSettings("ConnectionTimedOut")
    RE_REGISTERED = StatEventTypeSettings("ConnectionReRegistered")
    GROUP_CHANGED = StatEventTypeSettings("ConnectionDDoSGroupChanged")
    CONNECTION_DISCONNECTED = StatEventTypeSettings("ConnectionDisconnected")
