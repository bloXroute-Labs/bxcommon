from bxcommon.models.serializeable_enum import SerializableEnum


class BlockchainNetworkEnvironment(SerializableEnum):
    PRODUCTION = "PRODUCTION"
    DEVELOPMENT = "DEVELOPMENT"
