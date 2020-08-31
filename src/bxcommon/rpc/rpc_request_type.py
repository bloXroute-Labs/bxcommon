from bxcommon.models.serializeable_enum import SerializeableEnum


class RpcRequestType(SerializeableEnum):
    BLXR_TX = 0
    GATEWAY_STATUS = 1
    STOP = 2
    MEMORY = 3
    PEERS = 4
    BDN_PERFORMANCE = 5
    HEALTHCHECK = 6
    PING = 7
    SUBSCRIBE = 8
    UNSUBSCRIBE = 9
    QUOTA_USAGE = 10
    MEMORY_USAGE = 11
    TX_STATUS = 12
    BLXR_ETH_CALL = 13
