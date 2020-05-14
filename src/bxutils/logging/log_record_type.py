from enum import Enum


class LogRecordType(Enum):
    Stats = "stats"
    BX = "bx"
    BlockInfo = "stats.blocks.events"
    BlockPropagationInfo = "stats.blocks.events.p"
    BdnPerformanceStats = "stats.bdn_performance"
    TransactionInfo = "stats.transactions.events"
    TransactionPropagationInfo = "stats.transactions.events.p"
    TransactionStats = "stats.transactions.summary"
    PublicApiPerformance = "stats.publicapi.performance"
    Throughput = "stats.throughput"
    Memory = "stats.memory"
    NodeStatus = "stats.node.status"
    NodeInfo = "stats.node.info"
    NodeEvent = "stats.node.event"
    NetworkInfo = "stats.network.info"
    ConnectionState = "stats.connection_state"
    BlockCleanup = "bx.cleanup.block"
    TransactionCleanup = "bx.cleanup.transaction"
    BxMemory = "bx.memory"
    Recovery = "stats.recovery"
    TransactionHistogram = "bx.transaction.histogram"
    TransactionAudit = "stats.transaction.audit"
    TransactionAuditSummary = "stats.transaction.audit.summary"
    TransactionStatus = "transaction.status"
    BlockAudit = "stats.block.audit"
    BlockAuditSummary = "stats.block.audit.summary"
    AuditUpdates = "stats.audit.updates"
    CustomerInfo = "stats.customer.info"
    ExecutionTimerInfo = "stats.execution.timer.info"
    TaskDuration = "stats.task_duration"
    NetworkContent = "network_content.stats"
    RoutingService = "routing.service"
    ConnectionHealth = "stats.connection_health"
    PerformanceTroubleshooting = "stats.performance.responsiveness"
    MessageHandlingTroubleshooting = "stats.performance.message_handling"
    AlarmTroubleshooting = "stats.performance.alarm"
    NetworkTroubleshooting = "stats.performance.network"
    RoutingTableStats = "stats.routing"
    GarbageCollection = "stats.gc"
    ShortIdAllocation = "sid.allocation"
    Config = "config"
    QuotaNotification = "stats.quota.notification"
    QuotaFillStatus = "stats.quota.fill"
