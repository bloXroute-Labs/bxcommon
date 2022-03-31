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
    TX_SERVICE = 14
    ADD_BLOCKCHAIN_PEER = 15
    REMOVE_BLOCKCHAIN_PEER = 16
    _START_MONITOR_TRANSACTION_BY_HASH = 17
    STOP_MONITOR_TRANSACTION = 18
    LIST_ALL_MONITORED_TRANSACTIONS = 19
    BLXR_PRIVATE_TX = 20
    START_MONITOR_TRANSACTION = 21
    START_TRANSACTION_FEE_BUMP = 22
    STOP_TRANSACTION_FEE_BUMP = 23
    BLXR_TX_FEE_BUMP = 24
    NETWORK_TX_FEE_UPDATE = 25
    BLXR_SIMULATE_BUNDLE = 26
    BLXR_SUBMIT_BUNDLE = 27
    BLXR_PROFIT_SHARING_PRIVATE_TX = 28
    METAMASK_PRIVATE_TX = 29
    SIMULATE_ARB_ONLY_BUNDLE = 30
    SUBMIT_ARB_ONLY_BUNDLE = 31
    BLXR_INFO = 32
    BACKRUN_PRIVATE_TX = 33
    ADD_MEV_CREDIT = 34
    GET_MEV_CREDIT = 35
    ETH_SUBSCRIBE = 36
    PRIVATE_TX_BALANCE = 37
    BLXR_SUBMIT_MEGA_BUNDLE = 38
