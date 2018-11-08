from bxcommon.messages.abstract_message_factory import AbstractMessageFactory
from bxcommon.messages.btc.addr_btc_message import AddrBTCMessage
from bxcommon.messages.btc.block_btc_message import BlockBTCMessage
from bxcommon.messages.btc.btc_message import BTCMessage
from bxcommon.messages.btc.btc_message_type import BtcMessageType
from bxcommon.messages.btc.data_btc_message import GetBlocksBTCMessage, GetHeadersBTCMessage
from bxcommon.messages.btc.get_addr_btc_message import GetAddrBTCMessage
from bxcommon.messages.btc.header_btc_message import HeadersBTCMessage
from bxcommon.messages.btc.inventory_btc_message import GetDataBTCMessage, InvBTCMessage, NotFoundBTCMessage
from bxcommon.messages.btc.ping_btc_message import PingBTCMessage
from bxcommon.messages.btc.pong_btc_message import PongBTCMessage
from bxcommon.messages.btc.reject_btc_message import RejectBTCMessage
from bxcommon.messages.btc.send_headers_btc_message import SendHeadersBTCMessage
from bxcommon.messages.btc.tx_btc_message import TxBTCMessage
from bxcommon.messages.btc.ver_ack_btc_message import VerAckBTCMessage
from bxcommon.messages.btc.version_btc_message import VersionBTCMessage


class _BtcMessageFactory(AbstractMessageFactory):
    _MESSAGE_TYPE_MAPPING = {
        BtcMessageType.VERSION: VersionBTCMessage,
        BtcMessageType.VERACK: VerAckBTCMessage,
        BtcMessageType.PING: PingBTCMessage,
        BtcMessageType.PONG: PongBTCMessage,
        BtcMessageType.GET_ADDRESS: GetAddrBTCMessage,
        BtcMessageType.ADDRESS: AddrBTCMessage,
        BtcMessageType.INVENTORY: InvBTCMessage,
        BtcMessageType.GET_DATA: GetDataBTCMessage,
        BtcMessageType.NOT_FOUND: NotFoundBTCMessage,
        BtcMessageType.GET_HEADERS: GetHeadersBTCMessage,
        BtcMessageType.GET_BLOCKS: GetBlocksBTCMessage,
        BtcMessageType.TRANSACTIONS: TxBTCMessage,
        BtcMessageType.BLOCK: BlockBTCMessage,
        BtcMessageType.HEADERS: HeadersBTCMessage,
        BtcMessageType.REJECT: RejectBTCMessage,
        BtcMessageType.SEND_HEADERS: SendHeadersBTCMessage,
    }

    def __init__(self):
        super(_BtcMessageFactory, self).__init__()
        self.message_type_mapping = self._MESSAGE_TYPE_MAPPING
        self.base_message_type = BTCMessage


btc_message_factory = _BtcMessageFactory()
