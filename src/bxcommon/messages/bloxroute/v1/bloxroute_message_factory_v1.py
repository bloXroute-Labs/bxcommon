from bxcommon.messages.bloxroute.ack_message import AckMessage
from bxcommon.messages.bloxroute.bloxroute_message_factory import _BloxrouteMessageFactory
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.get_txs_message import GetTxsMessage
from bxcommon.messages.bloxroute.ping_message import PingMessage
from bxcommon.messages.bloxroute.pong_message import PongMessage
from bxcommon.messages.bloxroute.txs_message import TxsMessage
from bxcommon.messages.bloxroute.v1.broadcast_message_v1 import BroadcastMessageV1
from bxcommon.messages.bloxroute.v1.hello_message_v1 import HelloMessageV1
from bxcommon.messages.bloxroute.v1.key_message_v1 import KeyMessageV1
from bxcommon.messages.bloxroute.v1.tx_message_v1 import TxMessageV1


class _BloxrouteMessageFactoryV1(_BloxrouteMessageFactory):

    _MESSAGE_TYPE_MAPPING = {
        BloxrouteMessageType.HELLO: HelloMessageV1,
        BloxrouteMessageType.ACK: AckMessage,
        BloxrouteMessageType.PING: PingMessage,
        BloxrouteMessageType.PONG: PongMessage,
        BloxrouteMessageType.BROADCAST: BroadcastMessageV1,
        BloxrouteMessageType.TRANSACTION: TxMessageV1,
        BloxrouteMessageType.GET_TRANSACTIONS: GetTxsMessage,
        BloxrouteMessageType.TRANSACTIONS: TxsMessage,
        BloxrouteMessageType.KEY: KeyMessageV1
    }


bloxroute_message_factory_v1 = _BloxrouteMessageFactoryV1()
