from bxcommon.models.serializeable_enum import SerializeableEnum


class BlockchainNetworkType(SerializeableEnum):
    PERMISSIONED = "PERMISSIONED"
    PUBLIC = "PUBLIC"
