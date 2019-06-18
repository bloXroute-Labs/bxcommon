class BlockStatEventTypeSettings(object):
    def __init__(self, name, detailed_stat_event=False):
        self.name = name
        self.detailed_stat_event = detailed_stat_event


class BlockStatEventType(object):
    BLOCK_RECEIVED_FROM_BLOCKCHAIN_NODE = BlockStatEventTypeSettings("BlockReceivedFromBlockchainNode")
    BLOCK_RECEIVED_FROM_BLOCKCHAIN_NODE_IGNORE_SEEN = BlockStatEventTypeSettings(
        "BlockReceivedFromBlockchainNodeIgnoreSeen")
    COMPACT_BLOCK_RECEIVED_FROM_BLOCKCHAIN_NODE = BlockStatEventTypeSettings("CompactBlockReceivedFromBlockchainNode")
    COMPACT_BLOCK_RECEIVED_FROM_BLOCKCHAIN_NODE_IGNORE_SEEN = BlockStatEventTypeSettings(
        "CompactBlockReceivedFromBlockchainNodeIgnoreSeen")
    COMPACT_BLOCK_COMPRESSED = BlockStatEventTypeSettings(
        "CompactBlockCompressed")
    COMPACT_BLOCK_RECOVERY = BlockStatEventTypeSettings("CompactBlockRecovery")
    COMPACT_BLOCK_REQUEST_FULL = BlockStatEventTypeSettings("CompactBlockRequestFull")
    BLOCK_COMPRESSED = BlockStatEventTypeSettings("BlockCompressed")
    BLOCK_ENCRYPTED = BlockStatEventTypeSettings("BlockEncrypted")
    BLOCK_HOLD_REQUESTED = BlockStatEventTypeSettings("BlockHoldRequested", detailed_stat_event=True)
    BLOCK_HOLD_HELD_BLOCK = BlockStatEventTypeSettings("BlockHoldHeldBlock")
    BLOCK_HOLD_LIFTED = BlockStatEventTypeSettings("BlockHoldLifted", detailed_stat_event=True)
    BLOCK_HOLD_TIMED_OUT = BlockStatEventTypeSettings("BlockHoldTimeout")
    BLOCK_HOLD_SENT_BY_GATEWAY_TO_PEERS = BlockStatEventTypeSettings("BlockHoldSentByGatewayToPeers",
                                                                     detailed_stat_event=True)
    BLOCK_HOLD_RECEIVED_BY_RELAY_FROM_PEER = BlockStatEventTypeSettings("BlockHoldReceivedByRelayFromPeer",
                                                                        detailed_stat_event=True)
    BLOCK_HOLD_SENT_BY_RELAY_TO_PEERS = BlockStatEventTypeSettings("BlockHoldSentByRelayToPeers",
                                                                   detailed_stat_event=True)
    ENC_BLOCK_SENT_FROM_GATEWAY_TO_NETWORK = BlockStatEventTypeSettings("EncBlockSentFromGatewayToNetwork",
                                                                        detailed_stat_event=True)
    ENC_BLOCK_CUT_THROUGH_SEND_START = BlockStatEventTypeSettings("EncBlockCutThroughSendStart")
    ENC_BLOCK_CUT_THROUGH_SEND_END = BlockStatEventTypeSettings("EncBlockCutThroughSendEnd")
    ENC_BLOCK_CUT_THROUGH_RECEIVE_START = BlockStatEventTypeSettings("EncBlockCutThroughReceiveStart")
    ENC_BLOCK_CUT_THROUGH_RECEIVE_END = BlockStatEventTypeSettings("EncBlockCutThroughReceiveEnd")
    ENC_BLOCK_CUT_THROUGH_IGNORE_SEEN_BLOCK = BlockStatEventTypeSettings("EncBlockCutThroughIgnoreSeenBlock")
    ENC_BLOCK_RECEIVED_BY_GATEWAY_FROM_NETWORK = BlockStatEventTypeSettings("EncBlockReceivedByGatewayFromNetwork")
    ENC_BLOCK_DECRYPTED_SUCCESS = BlockStatEventTypeSettings("EncBlockDecryptedSuccess")
    ENC_BLOCK_DECRYPTION_ERROR = BlockStatEventTypeSettings("EncBlockDecryptionError")
    ENC_BLOCK_SENT_BLOCK_RECEIPT = BlockStatEventTypeSettings("EncBlockSentBlockReceipt", detailed_stat_event=True)
    ENC_BLOCK_RECEIVED_BLOCK_RECEIPT = BlockStatEventTypeSettings("EncBlockReceivedBlockReceipt")
    ENC_BLOCK_PROPAGATION_NEEDED = BlockStatEventTypeSettings("EncBlockPropagationNeeded")
    BX_BLOCK_PROPAGATION_REQUESTED_BY_PEER = BlockStatEventTypeSettings("BxBlockPropagationRequestedByPeer")
    BLOCK_DECOMPRESSED_IGNORE_SEEN = BlockStatEventTypeSettings("BlockDecompressedIgnoreSeen")
    BLOCK_DECOMPRESSED_SUCCESS = BlockStatEventTypeSettings("BlockDecompressedSuccess")
    BLOCK_DECOMPRESSED_WITH_UNKNOWN_TXS = BlockStatEventTypeSettings("BlockDecompressedWithUnknownTxs")
    BLOCK_RECOVERY_STARTED = BlockStatEventTypeSettings("BlockRecoveryStarted")
    BLOCK_RECOVERY_REPEATED = BlockStatEventTypeSettings("BlockRecoveryRepeated")
    BLOCK_RECOVERY_COMPLETED = BlockStatEventTypeSettings("BlockRecoveryCompleted")
    BLOCK_SENT_TO_BLOCKCHAIN_NODE = BlockStatEventTypeSettings("BlockSentToBlockchainNode")
    ENC_BLOCK_KEY_SENT_FROM_GATEWAY_TO_NETWORK = BlockStatEventTypeSettings("EncBlockKeySentFromGatewayToNetwork")
    ENC_BLOCK_KEY_RECEIVED_BY_GATEWAY_FROM_NETWORK = BlockStatEventTypeSettings(
        "EncBlockKeyReceivedByGatewayFromNetwork")
    ENC_BLOCK_KEY_SENT_BY_GATEWAY_TO_PEERS = BlockStatEventTypeSettings("EncBlockKeySentByGatewayToPeers",
                                                                        detailed_stat_event=True)
    ENC_BLOCK_KEY_RECEIVED_BY_RELAY_FROM_PEER = BlockStatEventTypeSettings("EncBlockKeyReceivedByRelayFromPeer")
    ENC_BLOCK_KEY_SENT_BY_RELAY_TO_PEER = BlockStatEventTypeSettings("EncBlockKeySentByRelayToPeer")
    REMOTE_BLOCK_RECEIVED_BY_GATEWAY = BlockStatEventTypeSettings("RemoteBlockReceivedByGateway")
    REMOTE_BLOCK_REQUESTED_BY_GATEWAY = BlockStatEventTypeSettings("RemoteBlockRequestedByGateway")
