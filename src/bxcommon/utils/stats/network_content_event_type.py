from bxcommon.models.serializeable_enum import SerializeableEnum


class NetworkContent(SerializeableEnum):
    BLOCK_CONTENT = "NetworkContentBlock"
    BLOCK_TRANSACTIONS = "NetworkContentBlockTransactions"
    TRANSACTION_CONTENT = "NetworkContentTransaction"
