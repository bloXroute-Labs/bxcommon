from bxcommon.messages.bloxroute.ack_message import AckMessage
from bxcommon.messages.bloxroute.bloxroute_message_factory import _BloxrouteMessageFactory
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.get_txs_message import GetTxsMessage
from bxcommon.messages.bloxroute.v1.ping_message_v1 import PingMessageV1
from bxcommon.messages.bloxroute.v1.pong_message_v1 import PongMessageV1
from bxcommon.messages.bloxroute.txs_message import TxsMessage
from bxcommon.messages.bloxroute.broadcast_message import BroadcastMessage
from bxcommon.messages.bloxroute.v2.hello_message_v2 import HelloMessageV2
from bxcommon.messages.bloxroute.key_message import KeyMessage
from bxcommon.messages.bloxroute.tx_message import TxMessage


class _BloxrouteMessageFactoryV2(_BloxrouteMessageFactory):

    _MESSAGE_TYPE_MAPPING = {
        BloxrouteMessageType.HELLO: HelloMessageV2,
        BloxrouteMessageType.ACK: AckMessage,
        BloxrouteMessageType.PING: PingMessageV1,
        BloxrouteMessageType.PONG: PongMessageV1,
        BloxrouteMessageType.BROADCAST: BroadcastMessage,
        BloxrouteMessageType.TRANSACTION: TxMessage,
        BloxrouteMessageType.GET_TRANSACTIONS: GetTxsMessage,
        BloxrouteMessageType.TRANSACTIONS: TxsMessage,
        BloxrouteMessageType.KEY: KeyMessage
    }


bloxroute_message_factory_v2 = _BloxrouteMessageFactoryV2()

