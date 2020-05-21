from bxcommon.models.serializeable_enum import SerializeableEnum


class BdnServiceType(SerializeableEnum):
    MSG_QUOTA = "MSG_QUOTA"
    PERMIT = "PERMIT"
