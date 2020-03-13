from bxcommon.models.serializeable_enum import SerializeableEnum


class PlatformProvider(SerializeableEnum):
    ALIBABA = "ALIBABA"
    AWS = "AWS"
    AZURE = "AZURE"
    GOOGLE = "GOOGLE"
