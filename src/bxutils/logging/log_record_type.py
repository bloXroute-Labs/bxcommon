from enum import Enum


class LogRecordType(Enum):
    Stats = "stats"
    BX = "bx"
    BlockInfo = "stats.blocks.events"
    TransactionInfo = "stats.transactions.events"
    TransactionStats = "stats.transactions.summary"
    Throughput = "stats.throughput"
    Memory = "stats.memory"
    NodeInfo = "stats.node.info"
    NodeEvent = "stats.node.event"
    NetworkInfo = "stats.network.info"
    ConnectionState = "stats.connection_state"
    BlockCleanup = "bx.cleanup.block"
    TransactionCleanup = "bx.cleanup.transaction"
    BxMemory = "bx.memory"
    Recovery = "stats.recovery"
    TransactionHistogram = "bx.transaction.histogram"


