from bxcommon.models.serializeable_enum import SerializableEnum


class BlockchainNetworkType(SerializableEnum):
    PERMISSIONED = "PERMISSIONED"
    PUBLIC = "PUBLIC"
