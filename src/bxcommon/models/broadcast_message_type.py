from bxcommon.models.serializeable_enum import SerializeableEnum


class BroadcastMessageType(SerializeableEnum):
    BLOCK = "blck"
    CONSENSUS = "cons"
