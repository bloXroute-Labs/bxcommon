from bxcommon.models.serializeable_enum import SerializeableEnum


class BlockchainNetworkEnvironment(SerializeableEnum):
    PRODUCTION = "PRODUCTION"
    DEVELOPMENT = "DEVELOPMENT"
