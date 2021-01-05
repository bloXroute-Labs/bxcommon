from bxcommon.models.serializeable_enum import SerializeableEnum


class TimeIntervalType(SerializeableEnum):
    DAILY = "DAILY"
    WITHOUT_INTERVAL = "WITHOUT_INTERVAL"
