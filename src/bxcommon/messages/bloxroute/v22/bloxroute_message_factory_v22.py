from typing import Optional, Type, NamedTuple

from bxcommon.messages.abstract_message import AbstractMessage
from bxcommon.messages.abstract_message_factory import AbstractMessageFactory
from bxcommon.messages.bloxroute.bdn_performance_stats_message import BdnPerformanceStatsMessage
from bxcommon.messages.bloxroute.blockchain_network_message import RefreshBlockchainNetworkMessage
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.messages.bloxroute.ack_message import AckMessage
from bxcommon.messages.bloxroute.block_confirmation_message import BlockConfirmationMessage
from bxcommon.messages.bloxroute.block_holding_message import BlockHoldingMessage
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.broadcast_message import BroadcastMessage
from bxcommon.messages.bloxroute.compressed_block_txs_message import CompressedBlockTxsMessage
from bxcommon.messages.bloxroute.disconnect_relay_peer_message import DisconnectRelayPeerMessage
from bxcommon.messages.bloxroute.get_compressed_block_txs_message import GetCompressedBlockTxsMessage
from bxcommon.messages.bloxroute.get_tx_contents_message import GetTxContentsMessage
from bxcommon.messages.bloxroute.get_txs_message import GetTxsMessage
from bxcommon.messages.bloxroute.hello_message import HelloMessage
from bxcommon.messages.bloxroute.key_message import KeyMessage
from bxcommon.messages.bloxroute.notification_message import NotificationMessage
from bxcommon.messages.bloxroute.ping_message import PingMessage
from bxcommon.messages.bloxroute.pong_message import PongMessage
from bxcommon.messages.bloxroute.routing_update_message import RoutingUpdateMessage
from bxcommon.messages.bloxroute.transaction_cleanup_message import TransactionCleanupMessage
from bxcommon.messages.bloxroute.tx_contents_message import TxContentsMessage
from bxcommon.messages.bloxroute.tx_message import TxMessage
from bxcommon.messages.bloxroute.tx_service_sync_blocks_short_ids_message import \
    TxServiceSyncBlocksShortIdsMessage
from bxcommon.messages.bloxroute.tx_service_sync_complete_message import \
    TxServiceSyncCompleteMessage
from bxcommon.messages.bloxroute.tx_service_sync_req_message import TxServiceSyncReqMessage
from bxcommon.messages.bloxroute.tx_service_sync_txs_message import TxServiceSyncTxsMessage
from bxcommon.messages.bloxroute.txs_message import TxsMessage
from bxcommon.models.broadcast_message_type import BroadcastMessageType

from bxcommon.utils.object_hash import ConcatHash, Sha256Hash


class BroadcastMessagePreview(NamedTuple):
    is_full_header: bool
    block_hash: Optional[Sha256Hash]
    broadcast_type: Optional[BroadcastMessageType]
    message_id: Optional[ConcatHash]
    network_num: Optional[int]
    source_id: Optional[str]
    payload_length: Optional[int]


class _BloxrouteMessageFactoryV22(AbstractMessageFactory):
    _MESSAGE_TYPE_MAPPING = {
        BloxrouteMessageType.HELLO: HelloMessage,
        BloxrouteMessageType.ACK: AckMessage,
        BloxrouteMessageType.PING: PingMessage,
        BloxrouteMessageType.PONG: PongMessage,
        BloxrouteMessageType.BROADCAST: BroadcastMessage,
        BloxrouteMessageType.TRANSACTION: TxMessage,
        BloxrouteMessageType.GET_TRANSACTIONS: GetTxsMessage,
        BloxrouteMessageType.TRANSACTIONS: TxsMessage,
        BloxrouteMessageType.GET_TX_CONTENTS: GetTxContentsMessage,
        BloxrouteMessageType.TX_CONTENTS: TxContentsMessage,
        BloxrouteMessageType.KEY: KeyMessage,
        BloxrouteMessageType.BLOCK_HOLDING: BlockHoldingMessage,
        BloxrouteMessageType.DISCONNECT_RELAY_PEER: DisconnectRelayPeerMessage,
        BloxrouteMessageType.TX_SERVICE_SYNC_REQ: TxServiceSyncReqMessage,
        BloxrouteMessageType.TX_SERVICE_SYNC_BLOCKS_SHORT_IDS: TxServiceSyncBlocksShortIdsMessage,
        BloxrouteMessageType.TX_SERVICE_SYNC_TXS: TxServiceSyncTxsMessage,
        BloxrouteMessageType.TX_SERVICE_SYNC_COMPLETE: TxServiceSyncCompleteMessage,
        BloxrouteMessageType.BLOCK_CONFIRMATION: BlockConfirmationMessage,
        BloxrouteMessageType.TRANSACTION_CLEANUP: TransactionCleanupMessage,
        BloxrouteMessageType.NOTIFICATION: NotificationMessage,
        BloxrouteMessageType.BDN_PERFORMANCE_STATS: BdnPerformanceStatsMessage,
        BloxrouteMessageType.REFRESH_BLOCKCHAIN_NETWORK: RefreshBlockchainNetworkMessage,
        BloxrouteMessageType.GET_COMPRESSED_BLOCK_TXS: GetCompressedBlockTxsMessage,
        BloxrouteMessageType.COMPRESSED_BLOCK_TXS: CompressedBlockTxsMessage,
        BloxrouteMessageType.ROUTING_UPDATE: RoutingUpdateMessage,
    }

    def __init__(self) -> None:
        super(_BloxrouteMessageFactoryV22, self).__init__(self._MESSAGE_TYPE_MAPPING)

    def get_base_message_type(self) -> Type[AbstractMessage]:
        return AbstractBloxrouteMessage


bloxroute_message_factory_v22 = _BloxrouteMessageFactoryV22()
