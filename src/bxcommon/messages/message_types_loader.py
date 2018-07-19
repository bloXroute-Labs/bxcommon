# FIXME refactor the circular parent-child-parent dependencies in messages
# Messages depends on this type dict which depends on Messages
#   Suggest changing the messages impl to be a factory pattern
_msg_types = None
_btc_msg_types = None


def get_message_types():
    global _msg_types

    if _msg_types:
        return _msg_types

    from bxcommon.messages.ack_message import AckMessage
    from bxcommon.messages.broadcast_message import BroadcastMessage
    from bxcommon.messages.hello_message import HelloMessage
    from bxcommon.messages.ping_message import PingMessage
    from bxcommon.messages.pong_message import PongMessage
    from bxcommon.messages.tx_assign_message import TxAssignMessage
    from bxcommon.messages.tx_message import TxMessage
    from bxcommon.messages.get_txs_details_message import GetTxsDetailsMessage
    from bxcommon.messages.txs_details_message import TxsDetailsMessage

    _msg_types = {
        'hello': HelloMessage,
        'ack': AckMessage,
        'ping': PingMessage,
        'pong': PongMessage,
        'broadcast': BroadcastMessage,
        'tx': TxMessage,
        'txassign': TxAssignMessage,
        'gettxs': GetTxsDetailsMessage,
        'txs': TxsDetailsMessage
    }

    return _msg_types


def get_btc_message_types():
    global _btc_msg_types

    if _btc_msg_types:
        return _btc_msg_types

    from bxcommon.messages.btc.version_btc_message import VersionBTCMessage
    from bxcommon.messages.btc.ver_ack_btc_message import VerAckBTCMessage
    from bxcommon.messages.btc.ping_btc_message import PingBTCMessage
    from bxcommon.messages.btc.pong_btc_message import PongBTCMessage
    from bxcommon.messages.btc.get_addr_btc_message import GetAddrBTCMessage
    from bxcommon.messages.btc.addr_btc_message import AddrBTCMessage
    from bxcommon.messages.btc.inventory_btc_message import InvBTCMessage
    from bxcommon.messages.btc.inventory_btc_message import GetDataBTCMessage
    from bxcommon.messages.btc.inventory_btc_message import NotFoundBTCMessage
    from bxcommon.messages.btc.data_btc_message import GetHeadersBTCMessage
    from bxcommon.messages.btc.data_btc_message import GetBlocksBTCMessage
    from bxcommon.messages.btc.tx_btc_message import TxBTCMessage
    from bxcommon.messages.btc.block_btc_message import BlockBTCMessage
    from bxcommon.messages.btc.header_btc_message import HeadersBTCMessage
    from bxcommon.messages.btc.reject_btc_message import RejectBTCMessage
    from bxcommon.messages.btc.send_headers_btc_message import SendHeadersBTCMessage

    _btc_msg_types = {
        'version': VersionBTCMessage,
        'verack': VerAckBTCMessage,
        'ping': PingBTCMessage,
        'pong': PongBTCMessage,
        'getaddr': GetAddrBTCMessage,
        'addr': AddrBTCMessage,
        'inv': InvBTCMessage,
        'getdata': GetDataBTCMessage,
        'notfound': NotFoundBTCMessage,
        'getheaders': GetHeadersBTCMessage,
        'getblocks': GetBlocksBTCMessage,
        'tx': TxBTCMessage,
        'block': BlockBTCMessage,
        'headers': HeadersBTCMessage,
        'reject': RejectBTCMessage,
        'sendheaders': SendHeadersBTCMessage,
    }

    return _btc_msg_types
