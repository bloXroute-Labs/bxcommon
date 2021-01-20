from bxcommon.utils.stats.stat_event_logic_flags import StatEventLogicFlags
from bxcommon.utils.stats.stat_event_type_settings import StatEventTypeSettings


# pylint: disable=invalid-name
class TransactionStatEventType:
    TX_RECEIVED_FROM_BLOCKCHAIN_NODE = StatEventTypeSettings("TxReceivedFromBlockchainNode",
                                                             event_logic_flags=StatEventLogicFlags.SUMMARY)
    TX_RECEIVED_FROM_BLOCKCHAIN_NODE_IGNORE_SEEN = StatEventTypeSettings("TxReceivedFromBlockchainNodeIgnoreSeen")
    TX_SENT_FROM_GATEWAY_TO_PEERS = StatEventTypeSettings("TxSentFromGatewayToPeers",
                                                          event_logic_flags=StatEventLogicFlags.SUMMARY)
    TX_SENT_FROM_GATEWAY_TO_BLOCKCHAIN_NODE = StatEventTypeSettings(
        "TxSentFromGatewayToBlockchainNode", event_logic_flags=StatEventLogicFlags.SUMMARY, priority=True)
    TX_RECEIVED_BY_GATEWAY_FROM_PEER = StatEventTypeSettings("TxReceivedByGatewayFromPeer",
                                                             event_logic_flags=StatEventLogicFlags.SUMMARY)
    TX_RECEIVED_BY_GATEWAY_FROM_PEER_IGNORE_SEEN = StatEventTypeSettings("TxReceivedByGatewayFromPeerIgnoreSeen")
    TX_RECEIVED_BY_RELAY_FROM_PEER = StatEventTypeSettings("TxReceivedByRelayFromPeer",
                                                           event_logic_flags=StatEventLogicFlags.SUMMARY, priority=True)
    TX_RECEIVED_BY_RELAY_FROM_PEER_IGNORE_SEEN = StatEventTypeSettings(
        "TxReceivedByRelayFromPeerIgnoreSeen", priority=True)
    TX_RECEIVED_BY_RELAY_FROM_PEER_FULL_QUOTA_IGNORED = StatEventTypeSettings(
        "TxReceivedByRelayFromPeerFullQuotaIgnored"
    )
    TX_RECEIVED_BY_RELAY_FROM_PEER_DELAYED = StatEventTypeSettings(
        "TxReceivedByRelayFromPeerDelayed"
    )
    TX_RECEIVED_BY_RELAY_FROM_PEER_IGNORE_EXPIRED = StatEventTypeSettings("TxReceivedByRelayFromPeerIgnoreExpired")
    TX_SHORT_ID_ASSIGNED_BY_RELAY = StatEventTypeSettings("TxShortIdAssignedByRelay")
    TX_SHORT_ID_STORED_BY_GATEWAY = StatEventTypeSettings("TxShortIdStoredByGateway")
    TX_SENT_FROM_RELAY_TO_PEERS = StatEventTypeSettings(
        "TxSentFromRelayToPeers",
        event_logic_flags=StatEventLogicFlags.SUMMARY,
        priority=True
    )
    TX_SENT_FROM_RELAY_TO_PEER_SKIPPED_ULTRA_SLOW = StatEventTypeSettings(
        "TxSentFromRelayToPeerSkippedUltraSlow"
    )
    TX_CONTENTS_REQUEST_SENT_FROM_RELAY = StatEventTypeSettings("TxContentsRequestSentFromRelay")
    TX_CONTENTS_REPLY_SENT_BY_RELAY = StatEventTypeSettings("TxContentsReplySentFromRelay")
    TX_CONTENTS_REPLY_RECEIVED_BY_RELAY = StatEventTypeSettings("TxContentsReplyReceivedByRelay")
    TX_UNKNOWN_SHORT_IDS_REQUESTED_BY_GATEWAY_FROM_RELAY = StatEventTypeSettings(
        "TxUnknownShortIdsRequestedByGatewayFromRelay")
    TX_UNKNOWN_SHORT_IDS_REPLY_RECEIVED_BY_GATEWAY_FROM_RELAY = StatEventTypeSettings(
        "TxUnknownShortIdsReplyReceivedByGatewayFromRelay")
    TX_UNKNOWN_SHORT_IDS_REPLY_SENT_BY_RELAY_TO_GATEWAY = StatEventTypeSettings(
        "TxUnknownShortIdsReplySentByRelayToGateway")
    TX_UNKNOWN_TRANSACTION_FOUND_BY_RELAY = StatEventTypeSettings("TxUnknownTransactionFoundByRelay")
    TX_UNKNOWN_TRANSACTION_NOT_FOUND_BY_RELAY = StatEventTypeSettings("TxUnknownTransactionNotFoundByRelay")
    TX_UNKNOWN_TRANSACTION_RECEIVED_BY_GATEWAY_FROM_RELAY = StatEventTypeSettings(
        "TxUnknownTransactionReceivedByGatewayFromRelay"
    )
    TX_REMOVED_FROM_MEMORY = StatEventTypeSettings("TxRemovedFromMemory", event_logic_flags=StatEventLogicFlags.SUMMARY)
    TX_BLOCK_RECOVERY_STATS = StatEventTypeSettings("TxBlockRecoveryStats")
    TX_RECEIVED_FROM_RPC_REQUEST = StatEventTypeSettings("TxReceivedFromRpcRequest",
                                                                event_logic_flags=StatEventLogicFlags.SUMMARY)
    TX_RECEIVED_FROM_RPC_REQUEST_IGNORE_SEEN = StatEventTypeSettings(
        "TxReceivedFromRpcRequestIgnoreSeen"
    )
    TX_COUNTER_BLOCKED = StatEventTypeSettings("TxCounterBlocked")

    TX_CLOUD_API_REQUEST_RECEIVE = StatEventTypeSettings("TxCloudApiRequestReceive")
    TX_CLOUD_API_REQUEST_SENT = StatEventTypeSettings("TxCloudApiRequestSent")
    TX_CLOUD_API_RESPONSE_RECEIVE = StatEventTypeSettings("TxCloudApiResponseReceive")
    TX_CLOUD_API_RESPONSE_SENT = StatEventTypeSettings("TxCloudApiResponseSent")
    TX_RELAY_HTTPS_SERVER_REQUEST_RECEIVE = StatEventTypeSettings("TxRelayHttpsServerRequestReceive")
    TX_RELAY_HTTPS_SERVER_RESPONSE_SENT = StatEventTypeSettings("TxRelayHttpsServerResponseSent")
    TX_GATEWAY_RPC_RESPONSE_SENT = StatEventTypeSettings("TxGatewayRpcResponseSent")
    TX_RELAY_HTTPS_SERVER_REQUEST_IGNORE_SEEN = StatEventTypeSettings(
        "TxRelayHttpsServerRequestIgnoreSeen"
    )
    TX_VALIDATION_FAILED_GAS_PRICE = StatEventTypeSettings("TxValidationFailedGasPrice")
    TX_VALIDATION_FAILED_STRUCTURE = StatEventTypeSettings("TxValidationFailedStructure")
    TX_VALIDATION_FAILED_SIGNATURE = StatEventTypeSettings("TxValidationFailedSignature")
    TX_FROM_BDN_IGNORE_LOW_GAS_PRICE = StatEventTypeSettings("TxFromBdnIgnoreLowGasPrice")

    TX_BLOCKCHAIN_STATUS = StatEventTypeSettings("TxBlockchainStatus")
    TX_REUSE_SENDER_NONCE = StatEventTypeSettings("TxReuseSenderNonce")
