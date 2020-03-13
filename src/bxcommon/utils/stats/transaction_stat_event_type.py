from bxcommon.utils.stats.stat_event_logic_flags import StatEventLogicFlags
from bxcommon.utils.stats.stat_event_type_settings import StatEventTypeSettings


class TransactionStatEventType:
    TX_RECEIVED_FROM_BLOCKCHAIN_NODE = StatEventTypeSettings("TxReceivedFromBlockchainNode",
                                                             event_logic_flags=StatEventLogicFlags.SUMMARY)
    TX_RECEIVED_FROM_BLOCKCHAIN_NODE_IGNORE_SEEN = StatEventTypeSettings("TxReceivedFromBlockchainNodeIgnoreSeen")
    TX_SENT_FROM_GATEWAY_TO_PEERS = StatEventTypeSettings("TxSentFromGatewayToPeers",
                                                          event_logic_flags=StatEventLogicFlags.SUMMARY)
    TX_SENT_FROM_GATEWAY_TO_BLOCKCHAIN_NODE = StatEventTypeSettings("TxSentFromGatewayToBlockchainNode",
                                                                    event_logic_flags=StatEventLogicFlags.SUMMARY)
    TX_RECEIVED_BY_GATEWAY_FROM_PEER = StatEventTypeSettings("TxReceivedByGatewayFromPeer",
                                                             event_logic_flags=StatEventLogicFlags.SUMMARY)
    TX_RECEIVED_BY_GATEWAY_FROM_PEER_IGNORE_SEEN = StatEventTypeSettings("TxReceivedByGatewayFromPeerIgnoreSeen")
    TX_RECEIVED_BY_RELAY_FROM_PEER = StatEventTypeSettings("TxReceivedByRelayFromPeer",
                                                           event_logic_flags=StatEventLogicFlags.SUMMARY)
    TX_RECEIVED_BY_RELAY_FROM_PEER_IGNORE_SEEN = StatEventTypeSettings("TxReceivedByRelayFromPeerIgnoreSeen")
    TX_RECEIVED_BY_RELAY_FROM_PEER_IGNORE_EXPIRED = StatEventTypeSettings("TxReceivedByRelayFromPeerIgnoreExpired")
    TX_SHORT_ID_ASSIGNED_BY_RELAY = StatEventTypeSettings("TxShortIdAssignedByRelay")
    TX_SHORT_ID_STORED_BY_GATEWAY = StatEventTypeSettings("TxShortIdStoredByGateway")
    TX_SHORT_ID_EMPTY_IN_MSG_FROM_RELAY = StatEventTypeSettings("TxShortIdEmptyInMsgFromRelay")
    TX_SENT_FROM_RELAY_TO_PEERS = StatEventTypeSettings("TxSentFromRelayToPeers",
                                                        event_logic_flags=StatEventLogicFlags.SUMMARY)
    TX_UNKNOWN_SHORT_IDS_REQUESTED_BY_GATEWAY_FROM_RELAY = StatEventTypeSettings(
        "TxUnknownShortIdsRequestedByGatewayFromRelay")
    TX_UNKNOWN_SHORT_IDS_REPLY_RECEIVED_BY_GATEWAY_FROM_RELAY = StatEventTypeSettings(
        "TxUnknownShortIdsReplyReceivedByGatewayFromRelay")
    TX_UNKNOWN_SHORT_IDS_REPLY_SENT_BY_RELAY_TO_GATEWAY = StatEventTypeSettings(
        "TxUnknownShortIdsReplySentByRelayToGateway")
    TX_UNKNOWN_TRANSACTION_FOUND_BY_RELAY = StatEventTypeSettings("TxUnknownTransactionFoundByRelay")
    TX_UNKNOWN_TRANSACTION_NOT_FOUND_BY_RELAY = StatEventTypeSettings("TxUnknownTransactionNotFoundByRelay")
    TX_UNKNOWN_TRANSACTION_RECEIVED_BY_GATEWAY_FROM_RELAY = StatEventTypeSettings("TxUnknownTransactionReceivedByGatewayFromRelay")
    TX_REMOVED_FROM_MEMORY = StatEventTypeSettings("TxRemovedFromMemory", event_logic_flags=StatEventLogicFlags.SUMMARY)
    TX_BLOCK_RECOVERY_STATS = StatEventTypeSettings("TxBlockRecoveryStats")
    BDN_TX_RECEIVED_FROM_CLIENT_ACCOUNT = StatEventTypeSettings("BDNTxReceivedFromClientAccount",
                                                                event_logic_flags=StatEventLogicFlags.SUMMARY)
    BDN_TX_RECEIVED_FROM_CLIENT_ACCOUNT_IGNORE_SEEN = StatEventTypeSettings(
        "BDNTxReceivedFromClientAccountIgnoreSeen"
    )
